#!/usr/bin/env python3
"""
Consolidated AWS Bedrock Multi-Modal Application
Combines speech generation (Polly), image generation (Titan), and chat (Nova models)
"""

import os
import sys
import json
import logging
import traceback
import time
import tempfile
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError

# Import BedrockAgentCore if available
try:
    from bedrock_agentcore import BedrockAgentCoreApp
    from strands import Agent
    AGENTCORE_AVAILABLE = True
except ImportError:
    AGENTCORE_AVAILABLE = False
    print("BedrockAgentCore not available - running in standalone mode")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BedrockMultiModalApp:
    """Main application class for multi-modal AWS Bedrock operations"""
    
    def __init__(self):
        """Initialize AWS clients and agents"""
        self.bedrock_client = None
        self.polly_client = None
        self.agents = {}
        
        # Initialize AWS clients
        self._initialize_aws_clients()
        
        # Initialize agents if AgentCore is available
        if AGENTCORE_AVAILABLE:
            self._initialize_agents()
            self.app = BedrockAgentCoreApp()
        else:
            self.app = None
    
    def _initialize_aws_clients(self):
        """Initialize AWS service clients"""
        try:
            self.bedrock_client = boto3.client('bedrock-runtime')
            logger.info("Initialized Bedrock client")
        except Exception as e:
            logger.warning(f"Could not initialize Bedrock client: {e}")
        
        try:
            self.polly_client = boto3.client('polly')
            logger.info("Initialized Polly client")
        except Exception as e:
            logger.warning(f"Could not initialize Polly client: {e}")
    
    def _initialize_agents(self):
        """Initialize Bedrock agents for different models"""
        models = {
            "pro": "amazon.nova-pro-v1:0",
            "sonic": "amazon.nova-sonic-v1:0",
            "canvas": "amazon.nova-canvas-v1:0",
            "micro": "amazon.nova-micro-v1:0"
        }
        
        for name, model_id in models.items():
            try:
                self.agents[name] = Agent(model=model_id)
                logger.info(f"Initialized {name} agent")
            except Exception as e:
                logger.warning(f"Could not initialize {name} agent: {e}")
    
    # ==================== SPEECH GENERATION ====================
    
    def handle_speech(self, text: str, output_format: str = "mp3",
                     voice_id: str = "Joanna", language_code: str = "en-US",
                     output_dir: str = None) -> Dict[str, Any]:
        """
        Generate speech from text using AWS Polly
        
        Args:
            text: Text to convert to speech
            output_format: Output format ("mp3" or "mp4")
            voice_id: Voice to use for synthesis
            language_code: Language code for synthesis
            output_dir: Directory to save output files
        
        Returns:
            Dictionary with speech generation results
        """
        try:
            if not self.polly_client:
                return {
                    "error": "AWS Polly client not initialized",
                    "status": "error",
                    "suggestion": "Check AWS credentials and permissions"
                }
            
            # Validate input
            validation = self.validate_speech_request(text, output_format)
            if not validation["valid"]:
                return {
                    "error": "Validation failed",
                    "errors": validation["errors"],
                    "status": "error"
                }
            
            # Set output directory
            if output_dir is None:
                output_dir = os.environ.get('TEST_OUTPUT_DIR', os.getcwd())
            os.makedirs(output_dir, exist_ok=True)
            
            # Limit text length
            max_chars = 3000
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning(f"Text truncated to {max_chars} characters")
            
            # Configure synthesis parameters
            synthesis_params = {
                'Text': text,
                'OutputFormat': 'mp3',
                'VoiceId': voice_id,
                'LanguageCode': language_code,
                'Engine': 'neural',
                'TextType': 'text'
            }
            
            # Perform synthesis
            response = self.polly_client.synthesize_speech(**synthesis_params)
            audio_data = response['AudioStream'].read()
            
            # Generate filename
            timestamp = str(int(time.time()))
            base_filename = f"speech_{timestamp}"
            
            # Handle output format
            if output_format.lower() == "mp4":
                try:
                    audio_data = self._convert_mp3_to_mp4(audio_data)
                    output_filename = f"{base_filename}.mp4"
                    actual_format = "mp4"
                except Exception as e:
                    logger.error(f"MP4 conversion failed: {e}")
                    output_filename = f"{base_filename}.mp3"
                    actual_format = "mp3"
            else:
                output_filename = f"{base_filename}.mp3"
                actual_format = "mp3"
            
            # Save file
            output_file_path = os.path.join(output_dir, output_filename)
            with open(output_file_path, 'wb') as f:
                f.write(audio_data)
            
            # Encode for API response
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                "result": "Speech synthesis completed successfully",
                "status": "success",
                "type": "speech_generation",
                "output_format": actual_format,
                "file_path": output_file_path,
                "filename": output_filename,
                "file_size_bytes": len(audio_data),
                "voice_used": voice_id,
                "language": language_code,
                "text_length": len(text),
                "audio_base64": audio_base64,
                "output_directory": output_dir
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return {
                "error": f"AWS Polly error ({error_code}): {error_message}",
                "status": "error",
                "aws_error_code": error_code
            }
        except Exception as e:
            logger.error(f"Error in speech generation: {e}")
            return {
                "error": str(e),
                "status": "error",
                "type": "speech_error"
            }
    
    def _convert_mp3_to_mp4(self, mp3_data: bytes) -> bytes:
        """Convert MP3 audio data to MP4 container format"""
        try:
            import subprocess
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
                mp3_file.write(mp3_data)
                mp3_path = mp3_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as mp4_file:
                mp4_path = mp4_file.name
            
            cmd = [
                'ffmpeg', '-y',
                '-i', mp3_path,
                '-c:a', 'aac',
                '-b:a', '128k',
                mp4_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                return mp3_data
            
            with open(mp4_path, 'rb') as f:
                mp4_data = f.read()
            
            os.unlink(mp3_path)
            os.unlink(mp4_path)
            
            return mp4_data
            
        except Exception as e:
            logger.error(f"Error converting MP3 to MP4: {e}")
            return mp3_data
    
    def validate_speech_request(self, text: str, output_format: str) -> Dict[str, Any]:
        """Validate speech generation request parameters"""
        errors = []
        
        if not text or len(text.strip()) == 0:
            errors.append("Text content is required")
        elif len(text) > 3000:
            errors.append("Text too long (max 3000 characters)")
        
        if output_format not in ["mp3", "mp4"]:
            errors.append("Output format must be 'mp3' or 'mp4'")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices from AWS Polly"""
        try:
            if not self.polly_client:
                return {
                    "error": "Polly client not initialized",
                    "status": "error"
                }
            
            response = self.polly_client.describe_voices()
            
            voices = {}
            for voice in response['Voices']:
                voices[voice['Id']] = {
                    'name': voice['Name'],
                    'language': voice['LanguageCode'],
                    'gender': voice['Gender'],
                    'engine': voice.get('SupportedEngines', [])
                }
            
            return {
                "voices": voices,
                "total_count": len(voices),
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    # ==================== IMAGE GENERATION ====================
    
    def handle_image_generation(self, prompt: str, image_params: Dict = None) -> Dict[str, Any]:
        """
        Generate images using Amazon Titan
        
        Args:
            prompt: Text description for image generation
            image_params: Additional parameters for image generation
        
        Returns:
            Dictionary with image generation results
        """
        try:
            if not self.bedrock_client:
                return {
                    "error": "Bedrock client not initialized",
                    "status": "error",
                    "suggestion": "Check AWS credentials and model access"
                }
            
            if image_params is None:
                image_params = {}
            
            # Prepare request for Titan
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
            
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            
            # Call Bedrock API
            response = self.bedrock_client.invoke_model(
                modelId="amazon.titan-image-generator-v2:0",
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            return {
                "result": response_body,
                "model": "titan",
                "status": "success",
                "type": "image_generation_response",
                "prompt": prompt,
                "parameters": image_params
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
            logger.error(f"Error in image generation: {e}")
            return {
                "error": str(e),
                "status": "error",
                "type": "image_generation_error"
            }
    
    # ==================== CHAT HANDLING ====================
    
    def handle_chat(self, model_type: str, prompt: str) -> Dict[str, Any]:
        """
        Handle chat requests using Nova models
        
        Args:
            model_type: Model to use (pro, sonic, canvas, micro)
            prompt: User prompt for chat
        
        Returns:
            Dictionary with chat response
        """
        try:
            if not AGENTCORE_AVAILABLE:
                return self._handle_chat_direct(model_type, prompt)
            
            if model_type not in self.agents:
                return {
                    "error": f"Model {model_type} not available",
                    "available_models": list(self.agents.keys()),
                    "status": "error"
                }
            
            agent = self.agents[model_type]
            
            # Invoke agent
            if hasattr(agent, 'invoke'):
                response = agent.invoke(prompt)
            elif callable(agent):
                response = agent(prompt)
            else:
                response = {"error": "Agent not callable"}
            
            # Extract response content
            content = self._extract_response_content(response)
            
            return {
                "result": content,
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
    
    def _handle_chat_direct(self, model_type: str, prompt: str) -> Dict[str, Any]:
        """Handle chat using direct Bedrock API calls"""
        try:
            if not self.bedrock_client:
                return {
                    "error": "Bedrock client not initialized",
                    "status": "error"
                }
            
            model_map = {
                "pro": "amazon.nova-pro-v1:0",
                "sonic": "amazon.nova-sonic-v1:0",
                "canvas": "amazon.nova-canvas-v1:0",
                "micro": "amazon.nova-micro-v1:0"
            }
            
            model_id = model_map.get(model_type, model_map["sonic"])
            
            # Prepare request
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            return {
                "result": response_body.get("content", response_body),
                "model_used": model_type,
                "status": "success",
                "type": "chat_response"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "error",
                "type": "chat_direct_error"
            }
    
    def _extract_response_content(self, response):
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
    
    # ==================== MAIN HANDLER ====================
    
    def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entrypoint for handling all requests
        
        Args:
            payload: Request payload with type and parameters
        
        Returns:
            Dictionary with operation results
        """
        try:
            # Parse payload
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"prompt": payload}
            elif payload is None:
                payload = {"type": "health"}
            
            request_type = payload.get("type", "chat")
            
            # Route request
            if request_type == "health":
                return self.health_check()
            
            elif request_type == "speech":
                return self.handle_speech(
                    text=payload.get("text", ""),
                    output_format=payload.get("output_format", "mp3"),
                    voice_id=payload.get("voice_id", "Joanna"),
                    language_code=payload.get("language_code", "en-US"),
                    output_dir=payload.get("output_dir")
                )
            
            elif request_type == "image_generation":
                return self.handle_image_generation(
                    prompt=payload.get("prompt", "A beautiful landscape"),
                    image_params=payload.get("image_params", {})
                )
            
            elif request_type == "chat":
                return self.handle_chat(
                    model_type=payload.get("model", "sonic"),
                    prompt=payload.get("prompt", "Hello!")
                )
            
            elif request_type == "voices":
                return self.get_available_voices()
            
            elif request_type == "models":
                return self.list_models()
            
            else:
                return {
                    "error": f"Unknown request type: {request_type}",
                    "valid_types": ["health", "speech", "image_generation", "chat", "voices", "models"],
                    "status": "error"
                }
                
        except Exception as e:
            logger.error(f"Error in invoke: {e}", exc_info=True)
            return {
                "error": str(e),
                "status": "error",
                "type": "invoke_error"
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            "status": "healthy",
            "services": {
                "bedrock": self.bedrock_client is not None,
                "polly": self.polly_client is not None,
                "agentcore": AGENTCORE_AVAILABLE
            },
            "available_features": {
                "chat": ["pro", "sonic", "canvas", "micro"],
                "image_generation": "titan",
                "speech_generation": "polly"
            },
            "framework": "bedrock_agentcore" if AGENTCORE_AVAILABLE else "standalone"
        }
    
    def list_models(self) -> Dict[str, Any]:
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
                    "use_for": ["general chat", "creative writing", "balanced tasks", "speech generation"]
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
                    "use_for": ["creating images from text descriptions"]
                },
                "polly": {
                    "purpose": "Text-to-speech synthesis",
                    "speed": "fast",
                    "quality": "high",
                    "use_for": ["generating audio from text", "voice synthesis"]
                }
            }
        }


# ==================== TEST RUNNER ====================

class TestRunner:
    """Test runner for the consolidated application"""
    
    def __init__(self, app: BedrockMultiModalApp):
        self.app = app
        self.results = []
    
    def test_function(self, test_name: str, func, *args, **kwargs) -> bool:
        """Test wrapper function"""
        try:
            print(f"\nRUNNING: {test_name}")
            result = func(*args, **kwargs)
            
            if isinstance(result, dict):
                print(f"RESULT: {json.dumps(result, indent=2, default=str)}")
            else:
                print(f"RESULT: {result}")
            
            self.results.append({
                "test": test_name,
                "success": True,
                "result": result
            })
            return True
            
        except Exception as e:
            print(f"ERROR: {test_name} failed: {str(e)}")
            print(f"TRACEBACK: {traceback.format_exc()}")
            
            self.results.append({
                "test": test_name,
                "success": False,
                "error": str(e)
            })
            return False
    
    def run_tests(self, test_cases: List[str] = None):
        """Run test suite"""
        if test_cases is None or 'all' in test_cases:
            test_cases = ['health', 'validation', 'voices', 'chat', 'speech', 'image', 'error']
        
        for test_case in test_cases:
            if test_case == 'health':
                self.test_function("Health Check", self.app.health_check)
                self.test_function("List Models", self.app.list_models)
            
            elif test_case == 'validation':
                self.test_function(
                    "Speech Input Validation",
                    self.app.validate_speech_request,
                    "Hello world", "mp3"
                )
            
            elif test_case == 'voices':
                self.test_function("Available Voices", self.app.get_available_voices)
            
            elif test_case == 'chat':
                self.test_function(
                    "Chat - Sonic Model",
                    self.app.handle_chat,
                    "sonic", "Hello, how are you today?"
                )
                self.test_function(
                    "Chat - Micro Model",
                    self.app.handle_chat,
                    "micro", "What is 2+2?"
                )
            
            elif test_case == 'speech':
                self.test_function(
                    "MP3 Generation",
                    self.app.handle_speech,
                    "Hello, thank you for calling our customer service. How may I assist you today?",
                    "mp3"
                )
                self.test_function(
                    "MP4 Generation",
                    self.app.handle_speech,
                    "Please hold while we connect you to the next available representative.",
                    "mp4"
                )
            
            elif test_case == 'image':
                self.test_function(
                    "Image Generation",
                    self.app.handle_image_generation,
                    "A serene mountain landscape at sunset",
                    {"width": 512, "height": 512}
                )
            
            elif test_case == 'error':
                self.test_function(
                    "Error Handling - Invalid Format",
                    self.app.handle_speech,
                    "Test", "wav"
                )
                self.test_function(
                    "Error Handling - Empty Text",
                    self.app.handle_speech,
                    "", "mp3"
                )
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        success_count = sum(1 for r in self.results if r["success"])
        total_count = len(self.results)
        print(f"Passed: {success_count}/{total_count}")
        
        if success_count < total_count:
            print("\nFailed tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result.get('error', 'Unknown error')}")
        
        return self.results


# ==================== CUSTOMER SERVICE HELPERS ====================

def generate_customer_service_prompts():
    """Generate various customer service prompts for testing"""
    return {
        "greeting": "Hello and welcome to our customer service. Thank you for calling. "
                   "My name is Alex, and I'm here to assist you today. How may I help you?",
        
        "hold_message": "Thank you for your patience. We are currently experiencing higher than normal call volume. "
                       "Please stay on the line and a representative will be with you as soon as possible. "
                       "Your call is important to us.",
        
        "transfer": "I'll be happy to transfer you to the appropriate department that can best assist you "
                   "with this request. Please hold while I connect you. Thank you for your patience.",
        
        "technical_support": "I understand you're experiencing technical difficulties. Let me help you resolve "
                           "this issue. I'll guide you through some troubleshooting steps to get this working "
                           "properly for you.",
        
        "billing_inquiry": "I can certainly help you with your billing inquiry. Let me access your account "
                         "information and review the details with you. Thank you for bringing this to our attention.",
        
        "closing": "Thank you for contacting us today. I hope I was able to resolve your concern satisfactorily. "
                  "Is there anything else I can help you with? We truly appreciate your business and have a wonderful day."
    }


# ==================== AGENTCORE INTEGRATION ====================

if AGENTCORE_AVAILABLE:
    # Create global app instance for AgentCore
    bedrock_app = BedrockMultiModalApp()
    app = bedrock_app.app
    
    # Register main entrypoint
    @app.entrypoint
    def invoke(payload):
        """Main entrypoint for AgentCore framework"""
        return bedrock_app.invoke(payload)
    
    # Register additional routes if supported
    try:
        @app.route("/health")
        def health_check(payload=None):
            return bedrock_app.health_check()
        
        @app.route("/models")
        def list_models(payload=None):
            return bedrock_app.list_models()
        
        @app.route("/voices")
        def get_voices(payload=None):
            return bedrock_app.get_available_voices()
        
    except Exception as e:
        logger.warning(f"Routes not supported by framework: {e}")


# ==================== MAIN EXECUTION ====================

def main():
    """Main function for standalone execution"""
    print("AWS Bedrock Multi-Modal Application")
    print("="*60)
    
    # Create application instance
    app = BedrockMultiModalApp()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # Run tests
            test_cases = sys.argv[2:] if len(sys.argv) > 2 else ['all']
            runner = TestRunner(app)
            runner.run_tests(test_cases)
        
        elif command == "chat":
            # Interactive chat mode
            model = sys.argv[2] if len(sys.argv) > 2 else "sonic"
            prompt = input(f"Enter prompt for {model} model: ")
            result = app.handle_chat(model, prompt)
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "speech":
            # Generate speech
            text = sys.argv[2] if len(sys.argv) > 2 else "Hello, this is a test."
            result = app.handle_speech(text)
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "image":
            # Generate image
            prompt = sys.argv[2] if len(sys.argv) > 2 else "A beautiful landscape"
            result = app.handle_image_generation(prompt)
            print(json.dumps(result, indent=2, default=str))
        
        elif command == "server":
            # Start server mode if AgentCore is available
            if AGENTCORE_AVAILABLE and app.app:
                logger.info("Starting AgentCore server on port 8080...")
                try:
                    app.app.run(host="0.0.0.0", port=8080, debug=True)
                except Exception as e:
                    logger.error(f"Failed to start server: {e}")
            else:
                print("AgentCore not available - cannot start server mode")
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: python app.py [test|chat|speech|image|server] [options]")
    
    else:
        # Default: run basic tests
        print("\nRunning basic functionality tests...")
        runner = TestRunner(app)
        runner.run_tests(['health', 'validation'])
        
        print("\n" + "="*60)
        print("To run full tests: python app.py test all")
        print("To start server: python app.py server")
        print("To chat: python app.py chat [model]")
        print("To generate speech: python app.py speech 'text to speak'")
        print("To generate image: python app.py image 'image description'")


if __name__ == "__main__":
    main()
