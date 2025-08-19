import unittest
import json
import requests
import base64
import time
from unittest.mock import patch, MagicMock

class TestBedrockAgentCore(unittest.TestCase):
    """
    Test cases for Bedrock AgentCore application
    """
    
    def setUp(self):
        """Set up test configuration"""
        self.base_url = "http://localhost:8080"
        self.headers = {"Content-Type": "application/json"}
        
    def test_health_check(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("models_available", data)
        self.assertIsInstance(data["models_available"], list)
    
    def test_entrypoint_default(self):
        """Test the main entrypoint with default parameters"""
        payload = {"prompt": "Hello, how are you?"}
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)
        self.assertIn("model_used", data)
        self.assertEqual(data["status"], "success")
    
    def test_entrypoint_pro_model(self):
        """Test entrypoint with Nova Pro model"""
        payload = {
            "model": "pro",
            "prompt": "Explain quantum computing in simple terms."
        }
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model_used"], "pro")
        self.assertIn("result", data)
    
    def test_entrypoint_micro_model(self):
        """Test entrypoint with Nova Micro model"""
        payload = {
            "model": "micro",
            "prompt": "What is 2+2?"
        }
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model_used"], "micro")
    
    def test_chat_route_valid_model(self):
        """Test chat route with valid model"""
        payload = {"prompt": "Tell me a joke"}
        
        response = requests.post(
            f"{self.base_url}/chat/sonic",
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)
    
    def test_chat_route_invalid_model(self):
        """Test chat route with invalid model"""
        payload = {"prompt": "Hello"}
        
        response = requests.post(
            f"{self.base_url}/chat/invalid_model",
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)  # App doesn't return HTTP errors
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid model", data["error"])
    
    def test_generate_image_basic(self):
        """Test basic image generation"""
        payload = {
            "prompt": "A serene mountain landscape at sunset"
        }
        
        response = requests.post(
            f"{self.base_url}/generate-image",
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model"], "titan")
        self.assertIn("result", data)
    
    def test_generate_image_with_params(self):
        """Test image generation with custom parameters"""
        payload = {
            "prompt": "A futuristic city with flying cars",
            "image_params": {
                "width": 512,
                "height": 512,
                "cfg_scale": 8.0,
                "number_of_images": 1
            }
        }
        
        response = requests.post(
            f"{self.base_url}/generate-image",
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
    
    def test_analyze_image_missing_data(self):
        """Test image analysis without image data"""
        payload = {
            "text": "What do you see in this image?"
        }
        
        response = requests.post(
            f"{self.base_url}/analyze-image",
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("No image data provided", data["error"])
    
    def test_analyze_image_with_data(self):
        """Test image analysis with base64 encoded image"""
        # Create a small test image (1x1 PNG)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        payload = {
            "text": "Describe this image",
            "image": test_image_b64,
            "image_format": "png"
        }
        
        response = requests.post(
            f"{self.base_url}/analyze-image",
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["model"], "canvas")
    
    def test_malformed_json(self):
        """Test handling of malformed JSON"""
        response = requests.post(
            self.base_url,
            headers=self.headers,
            data='{"prompt": "test", malformed}'
        )
        
        # Should handle gracefully
        self.assertEqual(response.status_code, 200)
    
    def test_empty_payload(self):
        """Test handling of empty payload"""
        response = requests.post(
            self.base_url,
            headers=self.headers,
            data=json.dumps({})
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("result", data)  # Should use default prompt


class TestPerformanceAndLoad(unittest.TestCase):
    """Performance and load testing"""
    
    def setUp(self):
        self.base_url = "http://localhost:8080"
        self.headers = {"Content-Type": "application/json"}
    
    def test_concurrent_requests(self):
        """Test multiple concurrent requests"""
        import concurrent.futures
        import threading
        
        def make_request(i):
            payload = {"prompt": f"Test request {i}"}
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            return response.status_code == 200
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Most requests should succeed
        success_rate = sum(results) / len(results)
        self.assertGreater(success_rate, 0.8)
    
    def test_response_time(self):
        """Test response time for different models"""
        models = ["micro", "sonic", "pro"]
        
        for model in models:
            start_time = time.time()
            
            payload = {
                "model": model,
                "prompt": "Quick response test"
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.assertEqual(response.status_code, 200)
            # Response should be under 30 seconds
            self.assertLess(response_time, 30)
            print(f"{model} model response time: {response_time:.2f}s")


if __name__ == "__main__":
    # Run specific test suites
    unittest.main(verbosity=2)

