#!/usr/bin/env python3
"""
AWS Bedrock Multi-Modal Backend Server
Provides REST API endpoints for the web frontend
"""

import os
import sys
import json
import uuid
import logging
import traceback
import time
import tempfile
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError

# Web server imports
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

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
            # Set region explicitly
            region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION') or 'us-east-1'
            
            self.bedrock_client = boto3.client('bedrock-runtime', region_name=region)
            logger.info(f"Initialized Bedrock client in region: {region}")
        except Exception as e:
            logger.warning(f"Could not initialize Bedrock client: {e}")
        
        try:
            # Set region explicitly
            region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION') or 'us-east-1'
            
            self.polly_client = boto3.client('polly', region_name=region)
            logger.info(f"Initialized Polly client in region: {region}")
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
                     output_dir: str = "generated_speech") -> Dict[str, Any]:
        """Generate speech from text using AWS Polly"""
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
            import shutil
            
            # Check if ffmpeg is available
            if not shutil.which('ffmpeg'):
                logger.warning("FFmpeg not found. Cannot convert MP3 to MP4. Returning MP3 data.")
                return mp3_data
            
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
            
            # Cleanup
            try:
                os.unlink(mp3_path)
                os.unlink(mp4_path)
            except Exception as e:
                pass
            
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

    def generate_with_nova_canvas(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate image using Amazon Nova Canvas."""
        try:
            if not self.bedrock_client:
                return {
                    "error": "Bedrock client not initialized",
                    "status": "error"
                }

            body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt,
                },
                "imageGenerationConfig": {
                    "numberOfImages": kwargs.get("numberOfImages", 1),
                    "quality": kwargs.get("quality", "standard"),
                    "width": kwargs.get("width", 1024),
                    "height": kwargs.get("height", 1024),
                    "cfgScale": kwargs.get("cfgScale", 8.0),
                    "seed": kwargs.get("seed", 42)
                }
            }
            
            response = self.bedrock_client.invoke_model(
                modelId="amazon.nova-canvas-v1:0",
                body=json.dumps(body),
                contentType="application/json"
            )

            response_body = json.loads(response['body'].read())
            
            if 'images' in response_body and len(response_body['images']) > 0:
                images = response_body.get('images', [])
                if images:
                    # Save images to files
                    saved_files = []
                    for i, image_data in enumerate(images):
                        filename = f"canvas_image_{uuid.uuid4().hex[:8]}.png"
                        self._save_base64_image(image_data, filename)
                        saved_files.append(filename)
                    
                    return {
                        "result": {
                            "images": images,
                            "saved_files": saved_files
                        },
                        "model": "nova-canvas",
                        "status": "success",
                        "type": "image_generation_response",
                        "prompt": prompt
                    }
                else:
                    return {
                        "error": "No images returned from Canvas",
                        "status": "error"
                    }
            else:
                return {
                    "error": "No images in response",
                    "status": "error"
                }
            
        except Exception as e:
            logger.error(f"Error generating image with Nova Canvas: {e}")
            return {
                "error": str(e),
                "status": "error",
                "type": "image_generation_error"
            }
    
    def generate_with_titan_model(self, prompt: str, image_params: Dict = None) -> Dict[str, Any]:
        """Generate images using Amazon Titan"""
        try:
            if not self.bedrock_client:
                return {
                    "error": "Bedrock client not initialized",
                    "status": "error"
                }
            
            if image_params is None:
                image_params = {}
            
            request_body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt,
                },
                "imageGenerationConfig": {
                    "width": image_params.get("width", 1024),
                    "height": image_params.get("height", 1024),
                    "cfgScale": image_params.get("cfg_scale", 7.0),
                    "seed": image_params.get("seed", 0),
                    "numberOfImages": image_params.get("number_of_images", 1),
                    "quality": image_params.get("quality", "standard")
                }
            }
            
            logger.info(f"Generating image with Titan: {prompt[:100]}...")
            
            response = self.bedrock_client.invoke_model(
                modelId="amazon.titan-image-generator-v2:0",
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            if 'images' in response_body and len(response_body['images']) > 0:
                images = response_body.get('images', [])
                if images:
                    # Save images to files
                    saved_files = []
                    for i, image_data in enumerate(images):
                        filename = f"titan_image_{uuid.uuid4().hex[:8]}.png"
                        self._save_base64_image(image_data, filename)
                        saved_files.append(filename)
                    
                    return {
                        "result": {
                            "images": images,
                            "saved_files": saved_files
                        },
                        "model": "titan",
                        "status": "success",
                        "type": "image_generation_response",
                        "prompt": prompt,
                        "parameters": image_params
                    }
                else:
                    return {
                        "error": "No images returned from Titan",
                        "status": "error"
                    }
            else:
                return {
                    "error": "No images in response",
                    "status": "error"
                }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            return {
                "error": f"Bedrock API error: {error_code} - {error_message}",
                "status": "error",
                "type": "bedrock_api_error"
            }

        except Exception as e:
            logger.error(f"Error in image generation: {e}")
            return {
                "error": str(e),
                "status": "error",
                "type": "image_generation_error"
            }

    def _save_base64_image(self, base64_data: str, filename: str):
        """Save base64 encoded image data to file."""
        try:
            output_dir = "generated_images"
            os.makedirs(output_dir, exist_ok=True)
            
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(base64_data))
                
            logger.info(f"Image saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")
        
    # ==================== CHAT HANDLING ====================
    
    def handle_chat(self, model_type: str, prompt: str) -> Dict[str, Any]:
        """Handle chat requests using Nova models"""
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
            
            # Prepare request for Nova models
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": 1000,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract content from Nova response format
            content = ""
            if "output" in response_body and "message" in response_body["output"]:
                message = response_body["output"]["message"]
                if "content" in message:
                    for content_block in message["content"]:
                        if "text" in content_block:
                            content += content_block["text"]
            else:
                content = str(response_body)
            
            return {
                "result": content,
                "model_used": model_type,
                "status": "success",
                "type": "chat_response"
            }
            
        except Exception as e:
            logger.error(f"Error in direct chat: {e}")
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
        """Main entrypoint for handling all requests"""
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
                    output_dir=payload.get("output_dir", "generated_speech")
                )
            
            elif request_type == "image_generation":
                model = payload.get("model", "canvas")
                prompt = payload.get("prompt", "A beautiful landscape")
                image_params = payload.get("image_params", {})
                
                if model == "titan":
                    return self.generate_with_titan_model(prompt, image_params)
                else:
                    return self.generate_with_nova_canvas(prompt, **image_params)
            
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
                "agentcore": "not_required" if not AGENTCORE_AVAILABLE else True
            },
            "available_features": {
                "chat": ["pro", "sonic", "canvas", "micro"],
                "image_generation": ["canvas", "titan"],
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
                    "use_for": ["image analysis", "multimodal tasks", "vision tasks", "image generation"]
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


# ==================== FLASK WEB SERVER ====================

def create_flask_app(bedrock_app: BedrockMultiModalApp) -> Flask:
    """Create Flask application with API endpoints"""
    
    app = Flask(__name__)
    
    # CORS configuration - Allow Firebase and localhost
    CORS(app, origins=[
        # 'http://localhost:3000',
        # 'http://localhost:8080',
        'https://multimodal-agents.web.app',           # ← Your Firebase domain
        'https://multimodal-agents.firebaseapp.com',   # ← Alternative Firebase domain
        'https://multimodal-agents-production.up.railway.app',  # ← Your Railway domain
        '*'  # ← Temporary wildcard for testing
    ])
    
    @app.route('/', methods=['GET'])
    def root_endpoint():
        """Root endpoint - API information"""
        return jsonify({
            "service": "AWS Bedrock Multi-Modal API",
            "status": "online",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "main_api": "/api",
                "chat": "/chat", 
                "image": "/image",
                "speech": "/speech",
                "models": "/models",
                "voices": "/voices"
            },
            "documentation": "POST to /api with type parameter",
            "example": {
                "url": "/api",
                "method": "POST",
                "body": {
                    "type": "chat",
                    "model": "pro", 
                    "prompt": "Hello!"
                }
            }
        })

    @app.route('/favicon.ico')
    def favicon():
        return '', 204
    
    @app.route('/health', methods=['GET', 'POST'])
    def health_check():
        """Health check endpoint"""
        try:
            result = bedrock_app.health_check()
            return jsonify(result), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/models', methods=['GET', 'POST'])
    def list_models():
        """List available models"""
        try:
            result = bedrock_app.list_models()
            return jsonify(result), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/voices', methods=['GET', 'POST'])
    def get_voices():
        """Get available voices"""
        try:
            result = bedrock_app.get_available_voices()
            return jsonify(result), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/api', methods=['POST'])
    def main_endpoint():
        """Main API endpoint for all operations"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "No JSON data provided"
                }), 400
            
            result = bedrock_app.invoke(data)
            return jsonify(result), 200
            
        except Exception as e:
            logger.error(f"Error in main endpoint: {e}")
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/chat', methods=['POST'])
    def chat_endpoint():
        """Dedicated chat endpoint"""
        try:
            data = request.get_json()
            model = data.get('model', 'sonic')
            prompt = data.get('prompt', '')
            
            if not prompt:
                return jsonify({
                    "status": "error",
                    "error": "Prompt is required"
                }), 400
            
            result = bedrock_app.handle_chat(model, prompt)
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/image', methods=['POST'])
    def image_endpoint():
        """Dedicated image generation endpoint"""
        try:
            data = request.get_json()
            prompt = data.get('prompt', '')
            model = data.get('model', 'canvas')
            image_params = data.get('image_params', {})
            
            if not prompt:
                return jsonify({
                    "status": "error",
                    "error": "Prompt is required"
                }), 400
            
            if model == "titan":
                result = bedrock_app.generate_with_titan_model(prompt, image_params)
            else:
                result = bedrock_app.generate_with_nova_canvas(prompt, **image_params)
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.route('/speech', methods=['POST'])
    def speech_endpoint():
        """Dedicated speech generation endpoint"""
        try:
            data = request.get_json()
            text = data.get('text', '')
            voice_id = data.get('voice_id', 'Joanna')
            output_format = data.get('output_format', 'mp3')
            language_code = data.get('language_code', 'en-US')
            
            if not text:
                return jsonify({
                    "status": "error",
                    "error": "Text is required"
                }), 400
            
            result = bedrock_app.handle_speech(
                text=text,
                voice_id=voice_id,
                output_format=output_format,
                language_code=language_code
            )
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e)
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "status": "error",
            "error": "Endpoint not found",
            "available_endpoints": ["/", "/health", "/models", "/voices", "/chat", "/image", "/speech"]
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "status": "error",
            "error": "Internal server error"
        }), 500
    
    return app


# ==================== MAIN EXECUTION ====================

def main():
    """Main function for server execution"""
    print("AWS Bedrock Multi-Modal Application Server")
    print("="*60)
    
    # Create application instance
    bedrock_app = BedrockMultiModalApp()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "server" or command == "web":
            # Start Flask web server
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
            host = sys.argv[3] if len(sys.argv) > 3 else "0.0.0.0"
            
            flask_app = create_flask_app(bedrock_app)
            
            print(f"\n🚀 Starting web server on {host}:{port}")
            print(f"🌐 Backend API URL: http://{host}:{port}")
            print(f"🔧 Main API Endpoint: http://{host}:{port}/api")
            print(f"❤️ Health Check: http://{host}:{port}/health")
            print("\n💡 Available endpoints:")
            print("   POST /api       - Main API endpoint")
            print("   GET|POST /health - Health check")
            print("   GET|POST /models - List models") 
            print("   GET|POST /voices - List voices")
            print("   POST /chat      - Chat endpoint")
            print("   POST /image     - Image generation")
            print("   POST /speech    - Speech generation")
            print("\n🔄 Press Ctrl+C to stop the server")
            
            try:
                flask_app.run(
                    host=host,
                    port=port,
                    debug=False,
                    threaded=True
                )
            except KeyboardInterrupt:
                print("\n👋 Server stopped by user")
            except Exception as e:
                print(f"❌ Server error: {e}")
        
        elif command == "test":
            # Run tests
            from test_runner import TestRunner
            test_cases = sys.argv[2:] if len(sys.argv) > 2 else ['all']
            runner = TestRunner(bedrock_app)
            runner.run_tests(test_cases)
        
        elif command == "chat":
            # Interactive chat mode
            model = sys.argv[2] if len(sys.argv) > 2 else "sonic"
            prompt = input(f"Enter prompt for {model} model: ")
            result = bedrock_app.handle_chat(model, prompt)
            print(json.dumps(result, indent=2, default=str))
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: python app.py [server|test|chat] [options]")
    
    else:
        # Default: start web server
        print("\n🚀 Starting default web server on port 8080...")
        print("🌐 Backend will be accessible at: http://0.0.0.0:8080")
        print("🔧 Main API Endpoint: http://localhost:8080/api")
        print("❤️ Health Check: http://localhost:8080/health")
        flask_app = create_flask_app(bedrock_app)
        
        try:
            flask_app.run(
                host="0.0.0.0",
                port=8080,
                debug=False,
                threaded=True
            )
        except KeyboardInterrupt:
            print("\n👋 Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {e}")


if __name__ == "__main__":
    main()
    