import boto3
import json
import base64
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockAgentCoreApp:
    def __init__(self):
        """Initialize the Bedrock application with proper AWS configuration."""
        self.bedrock_client = None
        self.bedrock_agent_client = None
        self.setup_clients()
    
    def setup_clients(self):
        """Setup Bedrock clients with proper error handling."""
        try:
            # Initialize Bedrock Runtime client for direct API calls
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
            )
            
            # Initialize Bedrock Agent client if needed
            self.bedrock_agent_client = boto3.client(
                'bedrock-agent-runtime',
                region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
            )
            
            logger.info("Bedrock clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock clients: {e}")
            raise

class Agent:
    """Wrapper class for Bedrock models."""
    def __init__(self, model: str):
        self.model = model
        self.bedrock_client = boto3.client('bedrock-runtime')
        logger.info(f"Agent initialized with model: {model}")
    
    def invoke_text_model(self, prompt: str, **kwargs) -> str:
        """Invoke text-based models like Nova."""
        try:
            # Prepare the request body based on model type
            if "nova" in self.model.lower():
                body = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "inferenceConfig": {
                        "max_new_tokens": kwargs.get("max_tokens", 1000),
                        "temperature": kwargs.get("temperature", 0.7)
                    }
                }
            else:
                # Generic body structure
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": kwargs.get("max_tokens", 1000),
                        "temperature": kwargs.get("temperature", 0.7)
                    }
                }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract text based on model response format
            if "nova" in self.model.lower():
                return response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
            else:
                return response_body.get('results', [{}])[0].get('outputText', '')
                
        except Exception as e:
            logger.error(f"Error invoking text model {self.model}: {e}")
            return f"Error: {str(e)}"

class ImageGenerator:
    """Specialized class for image generation using Bedrock."""
    
    def __init__(self, app: BedrockAgentCoreApp):
        self.app = app
        self.titan_model_id = "amazon.titan-image-generator-v2:0"
        self.nova_canvas_model_id = "amazon.nova-canvas-v1:0"
    
    def generate_with_titan(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate image using Amazon Titan Image Generator."""
        try:
            # Get negative prompt with default value (Titan requires minimum 3 characters)
            negative_text = kwargs.get("negative_prompt", "blurry, low quality, distorted")
            if len(negative_text) < 3:
                negative_text = "blurry, low quality, distorted"
            
            # Prepare Titan-specific request body
            body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt,
                    "negativeText": negative_text,
                },
                "imageGenerationConfig": {
                    "numberOfImages": kwargs.get("num_images", 1),
                    "height": kwargs.get("height", 1024),
                    "width": kwargs.get("width", 1024),
                    "cfgScale": kwargs.get("cfg_scale", 8.0),
                    "seed": kwargs.get("seed", 42)
                }
            }
            
            logger.info(f"Generating image with Titan: {prompt}")
            
            response = self.app.bedrock_client.invoke_model(
                modelId=self.titan_model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract the base64 image data
            images = response_body.get('images', [])
            if images:
                image_data = images[0]
                
                # Save image to file
                filename = f"titan_image_{uuid.uuid4().hex[:8]}.png"
                self._save_base64_image(image_data, filename)
                
                logger.info(f"Image saved as: {filename}")
                return filename
            else:
                logger.error("No images returned from Titan")
                return None
                
        except Exception as e:
            logger.error(f"Error generating image with Titan: {e}")
            return None
    
    def generate_with_nova_canvas(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate image using Amazon Nova Canvas."""
        try:
            body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": f"Generate an image: {prompt}"
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": kwargs.get("max_tokens", 1000)
                }
            }
            
            logger.info(f"Generating image with Nova Canvas: {prompt}")
            
            response = self.app.bedrock_client.invoke_model(
                modelId=self.nova_canvas_model_id,
                body=json.dumps(body),
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract image data (format may vary)
            # This is a placeholder - adjust based on actual Nova Canvas response format
            output = response_body.get('output', {})
            message = output.get('message', {})
            content = message.get('content', [])
            
            for item in content:
                if 'image' in item:
                    image_data = item['image']['source']['bytes']
                    filename = f"nova_canvas_{uuid.uuid4().hex[:8]}.png"
                    self._save_base64_image(image_data, filename)
                    logger.info(f"Image saved as: {filename}")
                    return filename
            
            logger.error("No image data found in Nova Canvas response")
            return None
            
        except Exception as e:
            logger.error(f"Error generating image with Nova Canvas: {e}")
            return None
    
    def _save_base64_image(self, base64_data: str, filename: str):
        """Save base64 encoded image data to file."""
        try:
            # Ensure output directory exists
            output_dir = "generated_images"
            os.makedirs(output_dir, exist_ok=True)
            
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(base64_data))
                
            logger.info(f"Image saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")

def main():
    """Main function to demonstrate image generation capabilities."""
    
    # Initialize the application
    app = BedrockAgentCoreApp()
    
    try:
        # Initialize agents for different models
        logger.info("Initializing agents...")
        
        # Nova models - text generation
        pro_agent = Agent(model="amazon.nova-pro-v1:0")
        sonic_agent = Agent(model="amazon.nova-lite-v1:0")  # Corrected from sonic to lite
        micro_agent = Agent(model="amazon.nova-micro-v1:0")
        
        # Image generation
        image_generator = ImageGenerator(app)
        
        logger.info("All agents initialized successfully")
        
        # Example: Generate image descriptions using text models
        print("\n=== Generating Image Descriptions ===")
        
        prompts = [
            "Describe a serene mountain landscape at sunset",
            "Create a description for a futuristic city skyline",
            "Describe a cozy coffee shop interior"
        ]
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n--- Prompt {i}: {prompt} ---")
            
            # Try different Nova models
            pro_response = pro_agent.invoke_text_model(prompt, max_tokens=200)
            print(f"Nova Pro Response: {pro_response[:100]}...")
            
        # Example: Generate actual images
        print("\n=== Generating Images ===")
        
        image_prompts = [
            "A beautiful sunset over mountains with vibrant colors",
            "A modern minimalist coffee shop with natural lighting",
            "A futuristic cityscape with flying cars and neon lights"
        ]
        
        for i, img_prompt in enumerate(image_prompts, 1):
            print(f"\n--- Generating Image {i}: {img_prompt} ---")
            
            # Generate with Titan
            titan_result = image_generator.generate_with_titan(
                img_prompt,
                width=1024,
                height=1024,
                num_images=1,
                cfg_scale=8.0,
                negative_prompt="blurry, low quality, distorted, ugly, artifacts"
            )
            
            if titan_result:
                print(f"✅ Titan image generated: {titan_result}")
            else:
                print("❌ Titan image generation failed")
            
            # Optionally try Nova Canvas (uncomment if available)
            # canvas_result = image_generator.generate_with_nova_canvas(img_prompt)
            # if canvas_result:
            #     print(f"✅ Nova Canvas image generated: {canvas_result}")
            # else:
            #     print("❌ Nova Canvas image generation failed")
        
        print("\n=== Image Generation Complete ===")
        print("Check the 'generated_images' folder for output files.")
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    # Set up AWS credentials (make sure these are configured)
    # You can set these via environment variables, AWS CLI, or IAM roles
    
    print("Amazon Bedrock Image Generation App")
    print("===================================")
    print("Make sure your AWS credentials are configured!")
    print("Required environment variables:")
    print("- AWS_ACCESS_KEY_ID")
    print("- AWS_SECRET_ACCESS_KEY") 
    print("- AWS_DEFAULT_REGION (optional, defaults to us-east-1)")
    print()
    
    # Check if basic AWS configuration exists
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            print("❌ AWS credentials not found!")
            print("Please configure your AWS credentials using one of these methods:")
            print("1. AWS CLI: aws configure")
            print("2. Environment variables")
            print("3. IAM roles (if running on AWS)")
            exit(1)
        else:
            print("✅ AWS credentials found")
            
    except Exception as e:
        print(f"❌ AWS configuration error: {e}")
        exit(1)
    
    main()

