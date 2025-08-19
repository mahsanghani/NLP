from bedrock_agentcore import BedrockAgentCoreApp
import json
import logging
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

# Initialize Bedrock client for all models
try:
    bedrock_client = boto3.client('bedrock-runtime')
    logger.info("✅ Initialized Bedrock client successfully")
    
    # Model configurations - using direct Bedrock model IDs
    MODELS = {
        "pro": {
            "id": "amazon.nova-pro-v1:0",
            "type": "text",
            "max_tokens": 4000,
            "description": "Complex reasoning and analysis"
        },
        "sonic": {
            "id": "amazon.nova-lite-v1:0", 
            "type": "text",
            "max_tokens": 4000,
            "description": "Balanced speed and quality"
        },
        "canvas": {
            "id": "amazon.nova-canvas-v1:0",
            "type": "multimodal",
            "max_tokens": 4000,
            "description": "Image analysis and multimodal tasks"
        },
        "micro": {
            "id": "amazon.nova-micro-v1:0",
            "type": "text", 
            "max_tokens": 4000,
            "description": "Fast responses, cost-effective"
        },
        "titan": {
            "id": "amazon.titan-image-generator-v2:0",
            "type": "image_generation",
            "description": "Image generation from text prompts"
        }
    }
    
    logger.info(f"Configured {len(MODELS)} models for Bedrock")
    
except Exception as e:
    logger.error(f"❌ Failed to initialize Bedrock client: {e}")
    bedrock_client = None
    MODELS = {}


def _invoke_bedrock_model(model_id, payload, model_type="text"):
    """Invoke any Bedrock model with proper error handling"""
    try:
        logger.info(f"Invoking {model_id} with payload type: {type(payload)}")
        
        # Convert payload to JSON string
        if isinstance(payload, dict):
            body = json.dumps(payload)
        elif isinstance(payload, str):
            body = payload
        else:
            body = json.dumps({"prompt": str(payload)})
        
        # Call Bedrock API
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=body,
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        logger.info(f"✅ Successfully invoked {model_id}")
        
        return {
            "success": True,
            "response": response_body,
            "model_id": model_id,
            "method": "bedrock_direct"
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        logger.error(f"❌ Bedrock API error for {model_id}: {error_code} - {error_message}")
        
        return {
            "success": False,
            "error": f"Bedrock API error: {error_code} - {error_message}",
            "error_code": error_code,
            "model_id": model_id,
            "suggestions": _get_error_suggestions(error_code)
        }
        
    except Exception as e:
        logger.error(f"❌ Unexpected error invoking {model_id}: {e}")
        
        return {
            "success": False,
            "error": str(e),
            "model_id": model_id,
            "type": "unexpected_error"
        }


def _get_error_suggestions(error_code):
    """Provide helpful suggestions based on error code"""
    suggestions = {
        "UnauthorizedOperation": [
            "Check AWS credentials with: aws sts get-caller-identity",
            "Verify Bedrock access permissions in IAM",
            "Ensure you have bedrock:InvokeModel permission"
        ],
        "AccessDeniedException": [
            "Request model access in AWS Bedrock console",
            "Check if model is available in your region",
            "Verify your AWS account has Bedrock access"
        ],
        "ValidationException": [
            "Check payload format for the specific model",
            "Verify required parameters are included",
            "Check parameter value ranges (e.g., max_tokens)"
        ],
        "ResourceNotFoundException": [
            "Verify model ID is correct",
            "Check if model is available in your region",
            "Try alternative model versions"
        ],
        "ThrottlingException": [
            "Reduce request frequency",
            "Implement exponential backoff",
            "Consider upgrading your service limits"
        ]
    }
    
    return suggestions.get(error_code, ["Check AWS documentation for this error code"])


def _extract_model_response(response_data, model_type):
    """Extract the actual content from model response"""
    try:
        if model_type == "image_generation":
            # Titan image response
            if "images" in response_data:
                return response_data["images"]
            elif "artifacts" in response_data:
                return response_data["artifacts"]
            else:
                return response_data
        
        else:
            # Text models - try different response formats
            if "completion" in response_data:
                return response_data["completion"]
            elif "content" in response_data:
                if isinstance(response_data["content"], list) and len(response_data["content"]) > 0:
                    return response_data["content"][0].get("text", response_data["content"])
                return response_data["content"]
            elif "text" in response_data:
                return response_data["text"]
            elif "message" in response_data:
                return response_data["message"]
            elif "response" in response_data:
                return response_data["response"]
            else:
                return response_data
                
    except Exception as e:
        logger.warning(f"Error extracting response: {e}")
        return response_data


# MAIN ENTRYPOINT
@app.entrypoint
def invoke(payload):
    """Main entrypoint - handles all requests using Bedrock client"""
    try:
        logger.info(f"Entrypoint received payload: {type(payload)}")
        
        # Check if Bedrock client is available
        if not bedrock_client:
            return {
                "error": "Bedrock client not initialized. Check AWS credentials and configuration.",
                "status": "error",
                "type": "bedrock_client_unavailable",
                "setup_help": [
                    "Run: aws configure",
                    "Ensure AWS credentials are set",
                    "Verify Bedrock access in your region"
                ]
            }
        
        # Handle different payload types
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {"prompt": payload}
        elif payload is None:
            payload = {"prompt": "Hello from Bedrock AgentCore!"}
        
        # Extract request information
        model_type = payload.get("model", "pro")
        user_prompt = payload.get("prompt", "Hello!")
        request_type = payload.get("type", "chat")
        
        logger.info(f"Processing: type={request_type}, model={model_type}")
        
        # Route based on request type
        if request_type == "health":
            return _handle_health_check()
        elif request_type == "models":
            return _handle_list_models()
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


def _handle_health_check():
    """Health check with Bedrock status"""
    try:
        # Test Bedrock connectivity
        bedrock_status = "unknown"
        if bedrock_client:
            try:
                # Try to list models as a connectivity test
                bedrock_client.list_foundation_models()
                bedrock_status = "connected"
            except Exception as e:
                bedrock_status = f"error: {str(e)[:100]}"
        
        return {
            "status": "healthy",
            "bedrock_status": bedrock_status,
            "models_available": list(MODELS.keys()),
            "framework": "bedrock_agentcore",
            "endpoint": "/invocations",
            "client_type": "direct_bedrock_api"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "bedrock_status": "error"
        }


def _handle_list_models():
    """List available models and their details"""
    return {
        "models": MODELS,
        "total_count": len(MODELS),
        "client_type": "direct_bedrock_api",
        "usage": {
            "chat": "Use model: pro|sonic|micro|canvas",
            "image_generation": "Use type: image_generation (automatically uses titan)",
            "image_analysis": "Use model: canvas with type: image_analysis"
        }
    }


def _handle_chat(model_type, user_prompt):
    """Handle chat requests using Bedrock text models"""
    try:
        # Validate model
        if model_type not in MODELS:
            return {
                "error": f"Unknown model: {model_type}",
                "available_models": list(MODELS.keys()),
                "status": "error"
            }
        
        model_config = MODELS[model_type]
        
        # Titan is for image generation only
        if model_type == "titan":
            return {
                "error": "Titan model is for image generation only. Use 'type': 'image_generation' or choose a different model for chat.",
                "status": "error",
                "available_chat_models": [k for k, v in MODELS.items() if v["type"] in ["text", "multimodal"]],
                "titan_usage": "Use with type: 'image_generation'"
            }
        
        # Prepare payload based on model type
        if model_config["type"] == "multimodal":
            # Canvas model format
            bedrock_payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": model_config["max_tokens"],
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ]
            }
        else:
            # Nova text models format
            bedrock_payload = {
                "messages": [
                    {
                        "role": "user", 
                        "content": user_prompt
                    }
                ],
                "max_tokens": model_config["max_tokens"],
                "temperature": 0.7
            }
        
        # Invoke model
        result = _invoke_bedrock_model(model_config["id"], bedrock_payload, model_config["type"])
        
        if result["success"]:
            content = _extract_model_response(result["response"], model_config["type"])
            return {
                "result": content,
                "model_used": model_type,
                "model_id": model_config["id"],
                "status": "success",
                "type": "chat_response",
                "method": "bedrock_direct"
            }
        else:
            return {
                "error": result["error"],
                "model_used": model_type,
                "model_id": model_config["id"],
                "status": "error",
                "type": "chat_error",
                "suggestions": result.get("suggestions", [])
            }
        
    except Exception as e:
        logger.error(f"Error in chat handling: {e}")
        return {
            "error": str(e),
            "status": "error",
            "type": "chat_error"
        }


def _handle_image_generation(payload):
    """Handle image generation using Titan with Bedrock client"""
    try:
        prompt = payload.get("prompt", "A beautiful landscape")
        image_params = payload.get("image_params", {})
        
        # Titan image generation payload
        bedrock_payload = {
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
        
        # Invoke Titan model
        result = _invoke_bedrock_model(MODELS["titan"]["id"], bedrock_payload, "image_generation")
        
        if result["success"]:
            content = _extract_model_response(result["response"], "image_generation")
            return {
                "result": content,
                "model": "titan",
                "model_id": MODELS["titan"]["id"],
                "status": "success",
                "type": "image_generation_response",
                "method": "bedrock_direct",
                "parameters_used": bedrock_payload["textToImageParams"]
            }
        else:
            return {
                "error": result["error"],
                "model": "titan", 
                "model_id": MODELS["titan"]["id"],
                "status": "error",
                "type": "image_generation_error",
                "suggestions": result.get("suggestions", [])
            }
        
    except Exception as e:
        logger.error(f"Error in image generation: {e}")
        return {
            "error": str(e),
            "status": "error",
            "type": "image_generation_error"
        }


def _handle_image_analysis(payload):
    """Handle image analysis using Canvas with Bedrock client"""
    try:
        text_prompt = payload.get("text", "Describe this image")
        image_data = payload.get("image")
        
        if not image_data:
            return {
                "error": "No image data provided. Include 'image' field with base64 encoded image data.",
                "status": "error",
                "required_format": "{'type': 'image_analysis', 'text': 'description', 'image': 'base64_data'}"
            }
        
        # Canvas multimodal payload
        bedrock_payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
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
        
        # Invoke Canvas model
        result = _invoke_bedrock_model(MODELS["canvas"]["id"], bedrock_payload, "multimodal")
        
        if result["success"]:
            content = _extract_model_response(result["response"], "multimodal")
            return {
                "result": content,
                "model": "canvas",
                "model_id": MODELS["canvas"]["id"],
                "status": "success", 
                "type": "image_analysis_response",
                "method": "bedrock_direct"
            }
        else:
            return {
                "error": result["error"],
                "model": "canvas",
                "model_id": MODELS["canvas"]["id"],
                "status": "error",
                "type": "image_analysis_error",
                "suggestions": result.get("suggestions", [])
            }
        
    except Exception as e:
        logger.error(f"Error in image analysis: {e}")
        return {
            "error": str(e),
            "status": "error",
            "type": "image_analysis_error"
        }


if __name__ == "__main__":
    logger.info("Starting Bedrock AgentCore with direct Bedrock client...")
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
