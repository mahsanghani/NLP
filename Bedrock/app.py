from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
import json
import logging
import boto3
from botocore.exceptions import ClientError

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

try:
    # Nova models - using correct model identifiers
    pro_agent = Agent(model="amazon.nova-pro-v1:0")
    sonic_agent = Agent(model="amazon.nova-lite-v1:0")
    canvas_agent = Agent(model="amazon.nova-canvas-v1:0")
    micro_agent = Agent(model="amazon.nova-micro-v1:0")
    
    # Titan Image Generator - Use direct Bedrock client instead of Agent wrapper
    # The Agent wrapper treats Titan like a conversational model, but it needs raw API calls
    try:
        bedrock_client = boto3.client('bedrock-runtime')
        titan_model_id = "amazon.titan-image-generator-v2:0"
        logger.info("Initialized direct Bedrock client for Titan")
        titan_agent = None  # We'll use bedrock_client directly
    except Exception as e:
        logger.warning(f"Could not initialize Bedrock client: {e}")
        # Fallback to Agent wrapper (will likely fail but we'll handle it)
        titan_agent = Agent(model="amazon.titan-image-generator-v2:0")
        bedrock_client = None
        titan_model_id = None
    
    logger.info("All agents initialized successfully")
    
except Exception as e:
    logger.error(f"Error initializing agents: {e}")
    # Fallback to a basic model if specific models fail
    pro_agent = Agent()
    bedrock_client = None
    titan_model_id = None


def _extract_response_content(response):
    """Helper function to extract content from agent response"""
    try:
        if hasattr(response, 'message'):
            return response.message
        elif hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'body'):
            return response.body
        elif isinstance(response, dict):
            for key in ['content', 'message', 'text', 'response', 'result']:
                if key in response:
                    return response[key]
            return response
        else:
            return str(response)
    except Exception as e:
        logger.error(f"Error extracting response content: {e}")
        return str(response)


def _safe_invoke_agent(agent, prompt):
    """Safely invoke agent with error handling"""
    try:
        logger.info(f"Invoking agent with prompt type: {type(prompt)}")
        
        # Try different invocation methods
        if hasattr(agent, 'invoke'):
            response = agent.invoke(prompt)
        elif callable(agent):
            response = agent(prompt)
        else:
            response = {"error": "Agent not callable", "agent_type": str(type(agent))}
        
        return response
        
    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        return {"error": str(e), "type": "agent_invocation_error"}


# MAIN ENTRYPOINT - This is the primary entry point for AgentCore
@app.entrypoint
def invoke(payload):
    """Main entrypoint for the application - handles all requests by default"""
    try:
        logger.info(f"Entrypoint received payload: {type(payload)}")
        
        # Handle different payload types
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {"prompt": payload}
        elif payload is None:
            payload = {"prompt": "Hello from AgentCore!"}
        
        # Extract request information
        model_type = payload.get("model", "pro")
        user_prompt = payload.get("prompt", "Hello from AgentCore!")
        request_type = payload.get("type", "chat")  # chat, image_generation, image_analysis
        
        logger.info(f"Processing: type={request_type}, model={model_type}")
        
        # Route based on request type
        if request_type == "health":
            return {
                "status": "healthy",
                "models_available": ["pro", "sonic", "canvas", "micro", "titan"],
                "framework": "bedrock_agentcore",
                "endpoint": "/invocations"
            }
        
        elif request_type == "image_generation":
            return _handle_image_generation(payload)
        
        elif request_type == "image_analysis":
            return _handle_image_analysis(payload)
        
        else:  # Default to chat
            return _handle_chat(model_type, user_prompt)
    
    except Exception as e:
        logger.error(f"Error in entrypoint: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "error",
            "type": "entrypoint_error"
        }


def _handle_chat(model_type, user_prompt):
    """Handle chat requests"""
    try:
        # IMPORTANT: Titan is for image generation only, not chat
        if model_type == "titan":
            return {
                "error": "Titan model is for image generation only. Use 'type': 'image_generation' or choose a different model (pro, sonic, canvas, micro) for chat.",
                "status": "error",
                "available_chat_models": ["pro", "sonic", "canvas", "micro"],
                "titan_usage": "Use with type: 'image_generation'"
            }
        
        # Select agent based on model type
        agent_map = {
            "pro": pro_agent,
            "sonic": sonic_agent,
            "canvas": canvas_agent,
            "micro": micro_agent
        }
        
        agent = agent_map.get(model_type, pro_agent)
        
        # Format prompt based on model
        if model_type == "canvas":
            # Canvas might need structured input for multimodal
            formatted_prompt = user_prompt  # Keep it simple for chat
        else:
            formatted_prompt = user_prompt
        
        response = _safe_invoke_agent(agent, formatted_prompt)
        
        return {
            "result": _extract_response_content(response),
            "model_used": model_type,
            "status": "success",
            "type": "chat_response"
        }
        
    except Exception as e:
        logger.error(f"Error in chat handling: {e}")
        return {
            "error": str(e),
            "status": "error",
            "type": "chat_error"
        }


def _handle_image_generation(payload):
    """Handle image generation requests using Titan with direct Bedrock API"""
    try:
        prompt = payload.get("prompt", "A beautiful landscape")
        image_params = payload.get("image_params", {})
        
        # If we have direct Bedrock client, use it
        if bedrock_client and titan_model_id:
            return _generate_image_with_bedrock(prompt, image_params)
        
        # Fallback to Agent wrapper (will likely fail but we'll try)
        logger.warning("Using Agent wrapper for Titan (may fail)")
        return _generate_image_with_agent(prompt, image_params)
        
    except Exception as e:
        logger.error(f"Error in image generation: {e}")
        return {
            "error": str(e),
            "status": "error",
            "type": "image_generation_error",
            "note": "Check Titan model configuration and AWS credentials"
        }


def _generate_image_with_bedrock(prompt, image_params):
    """Generate image using direct Bedrock client (recommended approach)"""
    try:
        # Correct Bedrock API format for Titan Image Generator
        request_body = {
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": prompt,
                "width": image_params.get("width", 1024),
                "height": image_params.get("height", 1024),
                "cfgScale": image_params.get("cfg_scale", 7.0),
                "seed": image_params.get("seed", 0),
                "numberOfImages": image_params.get("number_of_images", 1)
            }
        }
        
        logger.info(f"Calling Bedrock directly with: {request_body}")
        
        # Call Bedrock API directly
        response = bedrock_client.invoke_model(
            modelId=titan_model_id,
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        logger.info("Bedrock API call successful")
        
        return {
            "result": response_body,
            "model": "titan",
            "status": "success",
            "type": "image_generation_response",
            "method": "direct_bedrock_api"
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        return {
            "error": f"Bedrock API error: {error_code} - {error_message}",
            "status": "error",
            "type": "bedrock_api_error",
            "suggestion": "Check AWS credentials, model access permissions, and region"
        }
        
    except Exception as e:
        logger.error(f"Direct Bedrock call failed: {e}")
        return {
            "error": str(e),
            "status": "error",
            "type": "bedrock_direct_error"
        }


def _generate_image_with_agent(prompt, image_params):
    """Fallback: Try Agent wrapper with different formats"""
    try:
        if not titan_agent:
            return {
                "error": "Titan agent not available and no Bedrock client configured",
                "status": "error",
                "type": "titan_unavailable"
            }
        
        # Try different payload formats for Agent wrapper
        formats_to_try = [
            # Format 1: Direct Bedrock format (will likely fail due to message wrapping)
            {
                "name": "Direct Bedrock format",
                "payload": {
                    "taskType": "TEXT_IMAGE",
                    "textToImageParams": {
                        "text": prompt,
                        "width": image_params.get("width", 1024),
                        "height": image_params.get("height", 1024),
                        "cfgScale": image_params.get("cfg_scale", 7.0),
                        "seed": image_params.get("seed", 0),
                        "numberOfImages": image_params.get("number_of_images", 1)
                    }
                }
            },
            # Format 2: Simple prompt
            {
                "name": "Simple prompt",
                "payload": prompt
            },
            # Format 3: Prompt with parameters
            {
                "name": "Prompt with parameters",
                "payload": {
                    "prompt": prompt,
                    "parameters": image_params
                }
            }
        ]
        
        last_error = None
        for format_info in formats_to_try:
            try:
                logger.info(f"Trying Agent wrapper with {format_info['name']}")
                response = _safe_invoke_agent(titan_agent, format_info['payload'])
                
                # Check if response contains an error
                if isinstance(response, dict) and "error" in response:
                    last_error = response["error"]
                    logger.warning(f"{format_info['name']} failed: {last_error}")
                    continue
                
                # Success case
                return {
                    "result": _extract_response_content(response),
                    "model": "titan",
                    "status": "success",
                    "type": "image_generation_response",
                    "method": "agent_wrapper",
                    "format_used": format_info['name']
                }
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"{format_info['name']} failed with exception: {e}")
                continue
        
        # If all formats failed
        return {
            "error": f"All Agent wrapper formats failed. Last error: {last_error}",
            "status": "error",
            "type": "agent_wrapper_failed",
            "attempted_formats": [f['name'] for f in formats_to_try],
            "recommendation": "Use direct Bedrock API instead of Agent wrapper for Titan"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "error",
            "type": "agent_fallback_error"
        }


def _handle_image_analysis(payload):
    """Handle image analysis requests using Nova Canvas"""
    try:
        text_prompt = payload.get("text", "Describe this image")
        image_data = payload.get("image")
        
        if not image_data:
            return {
                "error": "No image data provided. Include 'image' field with base64 encoded image data.",
                "status": "error",
                "required_format": "{'type': 'image_analysis', 'text': 'description', 'image': 'base64_data'}"
            }
        
        # Try different Canvas payload formats
        logger.info(f"Attempting Canvas image analysis")
        
        # Format 1: Anthropic Claude format
        canvas_payload_v1 = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text_prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": f"image/{payload.get('image_format', 'png')}",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        }
        
        # Format 2: Simple multimodal format
        canvas_payload_v2 = {
            "text": text_prompt,
            "image": image_data,
            "image_format": payload.get('image_format', 'png')
        }
        
        # Format 3: Direct prompt with image reference
        canvas_payload_v3 = f"{text_prompt}\n[Image data: {image_data[:50]}...]"
        
        formats_to_try = [
            ("Anthropic Claude format", canvas_payload_v1),
            ("Simple multimodal format", canvas_payload_v2),
            ("Direct prompt format", canvas_payload_v3)
        ]
        
        last_error = None
        for format_name, payload_format in formats_to_try:
            try:
                logger.info(f"Trying Canvas {format_name}")
                response = _safe_invoke_agent(canvas_agent, payload_format)
                
                # Check if response contains an error
                if isinstance(response, dict) and "error" in response:
                    last_error = response["error"]
                    logger.warning(f"Canvas {format_name} failed: {last_error}")
                    continue
                
                # Success case
                return {
                    "result": _extract_response_content(response),
                    "model": "canvas",
                    "status": "success",
                    "type": "image_analysis_response",
                    "format_used": format_name
                }
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Canvas {format_name} failed with exception: {e}")
                continue
        
        # If all formats failed
        return {
            "error": f"All Canvas formats failed. Last error: {last_error}",
            "status": "error",
            "type": "image_analysis_error",
            "attempted_formats": [f[0] for f in formats_to_try],
            "note": "Canvas model may require specific authentication or different payload structure"
        }
        
    except Exception as e:
        logger.error(f"Error in image analysis: {e}")
        return {
            "error": str(e),
            "status": "error",
            "type": "image_analysis_error",
            "note": "Check Canvas model configuration and payload format"
        }


# Optional: Add routes if the framework supports them
try:
    @app.route("/health")
    def health_check(payload=None):
        """Health check route - may not be supported"""
        return {
            "status": "healthy",
            "models_available": ["pro", "sonic", "canvas", "micro", "titan"],
            "note": "Use /invocations endpoint for all requests",
            "chat_models": ["pro", "sonic", "canvas", "micro"],
            "image_generation": "titan",
            "image_analysis": "canvas"
        }
    
    @app.route("/models")
    def list_models(payload=None):
        """List available models and their purposes"""
        return {
            "models": {
                "pro": {
                    "purpose": "Complex reasoning and analysis",
                    "speed": "slower",
                    "quality": "highest",
                    "use_for": ["detailed analysis", "complex questions", "reasoning tasks"]
                },
                "sonic": {
                    "purpose": "Balanced speed and quality",
                    "speed": "fast",
                    "quality": "good",
                    "use_for": ["general chat", "creative writing", "balanced tasks"]
                },
                "micro": {
                    "purpose": "Fast responses, cost-effective",
                    "speed": "fastest",
                    "quality": "basic",
                    "use_for": ["simple questions", "quick responses", "basic tasks"]
                },
                "canvas": {
                    "purpose": "Multimodal (text + images)",
                    "speed": "moderate",
                    "quality": "high",
                    "use_for": ["image analysis", "multimodal tasks", "vision tasks"]
                },
                "titan": {
                    "purpose": "Image generation only",
                    "speed": "moderate",
                    "quality": "high",
                    "use_for": ["creating images from text descriptions"],
                    "note": "Not for chat - use type: 'image_generation'"
                }
            }
        }
    
except Exception as e:
    logger.warning(f"Routes not supported by framework: {e}")


if __name__ == "__main__":
    logger.info("Starting Bedrock AgentCore application...")
    try:
        # Test basic functionality
        logger.info("Testing basic functionality...")
        test_payload = {"prompt": "Hello, this is a test", "model": "micro"}
        test_response = invoke(test_payload)
        logger.info(f"Test response: {test_response}")
        
        # Test image generation
        logger.info("Testing image generation...")
        image_test_payload = {"type": "image_generation", "prompt": "A simple test image"}
        image_response = invoke(image_test_payload)
        logger.info(f"Image test response: {image_response}")
        
        # Start the application
        logger.info("Starting AgentCore server on port 8080...")
        app.run(host="0.0.0.0", port=8080, debug=True)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        print(f"Error starting app: {e}")
        
        # Try alternative startup methods
        try:
            logger.info("Trying alternative startup...")
            app.start()
        except Exception as e2:
            logger.error(f"Alternative startup failed: {e2}")
            
        try:
            logger.info("Trying basic run...")
            app.run()
        except Exception as e3:
            logger.error(f"Basic run failed: {e3}")
