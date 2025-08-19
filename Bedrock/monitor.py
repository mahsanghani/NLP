import time
import json
import requests
from datetime import datetime

def monitor_application():
    """Monitor the application health and performance"""
    base_url = "http://localhost:8080"
    
    while True:
        try:
            # Health check
            start_time = time.time()
            response = requests.get(f"{base_url}/health", timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                print(f"[{datetime.now()}] Health OK - Response time: {end_time - start_time:.2f}s")
            else:
                print(f"[{datetime.now()}] Health FAILED - Status: {response.status_code}")
            
            # Test a simple request
            test_payload = {"prompt": "Health check test"}
            start_time = time.time()
            response = requests.post(
                base_url, 
                json=test_payload, 
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    print(f"[{datetime.now()}] API OK - Response time: {end_time - start_time:.2f}s")
                else:
                    print(f"[{datetime.now()}] API WARNING - Unexpected response format")
            else:
                print(f"[{datetime.now()}] API FAILED - Status: {response.status_code}")
                
        except Exception as e:
            print(f"[{datetime.now()}] ERROR - {str(e)}")
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    print("Starting application monitoring...")
    monitor_application()
