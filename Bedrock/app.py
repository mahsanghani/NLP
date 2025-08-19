from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
import json
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

try:
    # Nova models - using correct model identifiers
    pro_agent = Agent(model="amazon.nova-pro-v1:0")
    sonic_agent = Agent(model="amazon.nova-lite-v1:0")  # Note: Nova Sonic may be "nova-lite"
    canvas_agent = Agent(model="amazon.nova-canvas-v1:0")
    micro_agent = Agent(model="amazon.nova-micro-v1:0")
    
    # Titan Image Generator
    titan_agent = Agent(model="amazon.titan-image-generator-v2:0")
    
    logger.info("All agents initialized successfully")
    
except Exception as e:
    logger.error(f"Error initializing agents: {e}")
    # Fallback to a basic model if specific models fail
    pro_agent = Agent()  # Use default model


def _extract_response_content(response):
    """Helper function to extract content from agent response"""
    try:
        # Handle different response formats
        if hasattr(response, 'message'):
            return response.message
        elif hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'body'):
            return response.body
        elif isinstance(response, dict):
            # Try common dictionary keys
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
        
        # Handle different agent invocation methods
        if hasattr(agent, 'invoke'):
            response = agent.invoke(prompt)
        elif hasattr(agent, 'call'):
            response = agent.call(prompt)
        elif hasattr(agent, '__call__'):
            response = agent(prompt)
        else:
            # Try direct invocation
            response = agent(prompt)
        
        return response
        
    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        return {"error": str(e), "type": "agent_invocation_error"}


@app.entrypoint
def invoke(payload):
    """Main entrypoint for the application"""
    try:
        logger.info(f"Received payload: {type(payload)} - {str(payload)[:200]}")
        
        # Handle different payload types
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {"prompt": payload}
        elif payload is None:
            payload = {}
        
        model_type = payload.get("model", "pro")  # Default to pro
        user_prompt = payload.get("prompt", "Hello from AgentCore!")
        
        logger.info(f"Processing request with model: {model_type}, prompt: {str(user_prompt)[:100]}")
        
        # Select agent based on model type
        agent_map = {
            "pro": pro_agent,
            "sonic": sonic_agent,
            "canvas": canvas_agent,
            "micro": micro_agent,
            "titan": titan_agent
        }
        
        agent = agent_map.get(model_type, pro_agent)
        
        # Handle different prompt formats based on model
        if model_type == "titan":
            # Titan expects specific format for image generation
            if isinstance(user_prompt, str):
                formatted_prompt = {
                    "taskType": "TEXT_IMAGE",
                    "textToImageParams": {
                        "text": user_prompt,
                        "width": 1024,
                        "height": 1024
                    }
                }
            else:
                formatted_prompt = user_prompt
        else:
            # Text models expect string prompts
            formatted_prompt = user_prompt
        
        # Safely invoke the agent
        response = _safe_invoke_agent(agent, formatted_prompt)
        
        return {
            "result": _extract_response_content(response),
            "model_used": model_type,
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Error in invoke: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "error",
            "type": "invoke_error"
        }


@app.route("/")
def root(payload):
    """Root endpoint - same as entrypoint"""
    return invoke(payload)


@app.route("/health")
def health_check(payload=None):
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "models_available": ["pro", "sonic", "canvas", "micro", "titan"],
            "timestamp": str(logging.time.time()) if hasattr(logging, 'time') else "unknown"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.route("/chat/<model>")
def chat_with_model(model, payload):
    """Route to chat with specific model"""
    try:
        logger.info(f"Chat route called with model: {model}")
        
        # Validate model parameter
        valid_models = ["pro", "sonic", "canvas", "micro", "titan"]
        if model not in valid_models:
            return {
                "error": f"Invalid model: {model}. Valid models: {valid_models}",
                "status": "error"
            }
        
        # Handle payload
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {"prompt": payload}
        elif payload is None:
            payload = {}
        
        user_prompt = payload.get("prompt", "Hello!")
        
        # Create request payload for main invoke function
        request_payload = {
            "model": model,
            "prompt": user_prompt
        }
        
        return invoke(request_payload)
    
    except Exception as e:
        logger.error(f"Error in chat_with_model: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "error",
            "type": "chat_route_error"
        }


@app.route("/generate-image")
def generate_image(payload):
    """Generate images using Titan"""
    try:
        logger.info("Generate image route called")
        
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON payload", "status": "error"}
        elif payload is None:
            payload = {}
        
        prompt = payload.get("prompt", "A beautiful landscape")
        image_params = payload.get("image_params", {})
        
        # Format for Titan Image Generator
        titan_payload = {
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
        
        response = _safe_invoke_agent(titan_agent, titan_payload)
        
        return {
            "result": _extract_response_content(response),
            "model": "titan",
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Error in generate_image: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "error",
            "type": "image_generation_error"
        }


@app.route("/analyze-image")
def analyze_image(payload):
    """Analyze images using Nova Canvas"""
    try:
        logger.info("Analyze image route called")
        
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON payload", "status": "error"}
        elif payload is None:
            return {"error": "No payload provided", "status": "error"}
        
        text_prompt = payload.get("text", "Describe this image")
        image_data = payload.get("image")  # Base64 encoded image
        
        if not image_data:
            return {
                "error": "No image data provided",
                "status": "error"
            }
        
        # Format for Nova Canvas multimodal input
        multimodal_input = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
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
        
        response = _safe_invoke_agent(canvas_agent, multimodal_input)
        
        return {
            "result": _extract_response_content(response),
            "model": "canvas",
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Error in analyze_image: {e}", exc_info=True)
        return {
            "error": str(e),
            "status": "error",
            "type": "image_analysis_error"
        }


# Add a catch-all route for debugging
@app.route("/<path>")
def catch_all(path, payload):
    """Catch-all route for debugging"""
    return {
        "error": f"Route not found: /{path}",
        "available_routes": [
            "/",
            "/health", 
            "/chat/<model>",
            "/generate-image",
            "/analyze-image"
        ],
        "status": "error"
    }


if __name__ == "__main__":
    logger.info("Starting Bedrock AgentCore application...")
    try:
        # Test agent initialization
        logger.info("Testing agent initialization...")
        test_response = _safe_invoke_agent(pro_agent, "Hello, test message")
        logger.info(f"Test response: {_extract_response_content(test_response)}")
        
        # Run the application
        logger.info("Starting server on port 8080...")
        app.run(host="0.0.0.0", port=8080)
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        print(f"Error starting app: {e}")

