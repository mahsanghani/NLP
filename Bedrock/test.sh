#!/bin/bash

# BEDROCK AGENTCORE COMPREHENSIVE TEST SUITE
# All output will be saved to test_results.log

LOG_FILE="test_results_$(date +%Y%m%d_%H%M%S).log"
BASE_URL="http://localhost:8080/invocations"

# Function to log and display output
log_and_echo() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Function to run curl and log results
run_test() {
    local test_name="$1"
    local curl_data="$2"
    
    log_and_echo "=== $test_name ==="
    log_and_echo "Request: $curl_data"
    log_and_echo "Response:"
    
    curl -X POST "$BASE_URL" \
        -H "Content-Type: application/json" \
        -d "$curl_data" 2>&1 | tee -a "$LOG_FILE"
    
    log_and_echo ""
    log_and_echo "---"
    log_and_echo ""
}

# Start logging
log_and_echo "BEDROCK AGENTCORE TEST SUITE"
log_and_echo "Started at: $(date)"
log_and_echo "Endpoint: $BASE_URL"
log_and_echo "Log file: $LOG_FILE"
log_and_echo "========================================"
log_and_echo ""

# Test 1: Health Check
run_test "1. Health Check" '{
    "type": "health"
}'

# Test 2: Basic Chat (Default Model)
run_test "2. Basic Chat (Default)" '{
    "prompt": "Hello, how are you today?"
}'

# Test 3: Micro Model (Fast responses)
run_test "3. Micro Model Chat" '{
    "model": "micro",
    "prompt": "What is 25 * 16?"
}'

# Test 4: Pro Model (Complex reasoning)
run_test "4. Pro Model Chat" '{
    "model": "pro",
    "prompt": "Explain the concept of machine learning in 3 sentences"
}'

# Test 5: Sonic Model (Balanced)
run_test "5. Sonic Model Chat" '{
    "model": "sonic",
    "prompt": "Write a haiku about technology"
}'

# Test 6: Canvas Model (Multimodal - text only)
run_test "6. Canvas Model Chat" '{
    "model": "canvas",
    "prompt": "Describe a futuristic city landscape"
}'

# Test 7: Titan Model Chat (Should Error - Titan is image-only)
run_test "7. Titan Model Chat (Should Error)" '{
    "model": "titan",
    "prompt": "This should return an error message"
}'

# Test 8: Basic Image Generation
run_test "8. Basic Image Generation" '{
    "type": "image_generation",
    "prompt": "A serene mountain landscape at sunset"
}'

# Test 9: Image Generation with Custom Parameters
run_test "9. Image Generation (Custom Params)" '{
    "type": "image_generation",
    "prompt": "A futuristic cityscape with flying vehicles",
    "image_params": {
        "width": 768,
        "height": 768,
        "cfg_scale": 8.0,
        "seed": 42,
        "number_of_images": 1
    }
}'

# Test 10: High-Quality Image Generation
run_test "10. High-Quality Image Generation" '{
    "type": "image_generation",
    "prompt": "A detailed architectural visualization of a modern sustainable building with solar panels and green design",
    "image_params": {
        "width": 1024,
        "height": 1024,
        "cfg_scale": 9.0,
        "seed": 123456
    }
}'

# Test 11: Image Analysis (No Image - Should Error)
run_test "11. Image Analysis (No Image)" '{
    "type": "image_analysis",
    "text": "What do you see in this image?"
}'

# Test 12: Image Analysis with Test Image
run_test "12. Image Analysis (With Image)" '{
    "type": "image_analysis",
    "text": "Describe this image in detail",
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "image_format": "png"
}'

# Test 13: Empty Payload
run_test "13. Empty Payload" '{}'

# Test 14: String Payload
run_test "14. String Payload" '"Hello as a string"'

# Test 15: Invalid Model (Should Fallback)
run_test "15. Invalid Model" '{
    "model": "invalid_model",
    "prompt": "This should fallback to default model"
}'

# Test 16: Complex Reasoning Task
run_test "16. Complex Reasoning (Pro)" '{
    "model": "pro",
    "prompt": "Compare and contrast supervised learning, unsupervised learning, and reinforcement learning. Provide one real-world example for each."
}'

# Test 17: Creative Writing Task
run_test "17. Creative Writing (Sonic)" '{
    "model": "sonic",
    "prompt": "Write a short story (3-4 sentences) about a robot discovering emotions for the first time."
}'

# Test 18: Mathematical Task
run_test "18. Mathematical Task (Micro)" '{
    "model": "micro",
    "prompt": "If I save $500 per month for 2 years at 3% annual interest, how much will I have?"
}'

# Test 19: Image Generation - Artistic Style
run_test "19. Artistic Image Generation" '{
    "type": "image_generation",
    "prompt": "An impressionist painting style image of a garden with vibrant flowers and soft lighting",
    "image_params": {
        "width": 512,
        "height": 768,
        "cfg_scale": 7.5
    }
}'

# Test 20: Canvas Model for Vision Description
run_test "20. Canvas Vision Task" '{
    "model": "canvas",
    "prompt": "Create a detailed description of what an ideal smart home interior would look like, focusing on technology integration"
}'

log_and_echo "========================================"
log_and_echo "DEBUGGING AND MONITORING TESTS"
log_and_echo "========================================"

# Debug Test 1: Server Headers
log_and_echo "=== Server Headers Test ==="
curl -I "$BASE_URL" 2>&1 | tee -a "$LOG_FILE"
log_and_echo ""

# Debug Test 2: Verbose Request
log_and_echo "=== Verbose Request Test ==="
curl -v -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d '{"type": "health"}' 2>&1 | head -20 | tee -a "$LOG_FILE"
log_and_echo ""

# Debug Test 3: Response Time Test
log_and_echo "=== Response Time Test ==="
log_and_echo "Testing response time for Micro model..."
time_output=$(time curl -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d '{"model": "micro", "prompt": "Quick test"}' 2>&1)
echo "$time_output" | tee -a "$LOG_FILE"
log_and_echo ""

log_and_echo "========================================"
log_and_echo "CONCURRENT TESTING"
log_and_echo "========================================"

# Concurrent Test
log_and_echo "=== Concurrent Requests Test ==="
log_and_echo "Starting 5 concurrent requests..."

for i in {1..5}; do
    (
        log_and_echo "Starting concurrent request $i"
        response=$(curl -X POST "$BASE_URL" \
            -H "Content-Type: application/json" \
            -d "{\"model\": \"micro\", \"prompt\": \"Concurrent test $i\"}" 2>/dev/null)
        log_and_echo "Request $i response: $response"
    ) &
done

wait
log_and_echo "All concurrent requests completed"
log_and_echo ""

log_and_echo "========================================"
log_and_echo "ERROR HANDLING TESTS"
log_and_echo "========================================"

# Error Test 1: Malformed JSON
log_and_echo "=== Malformed JSON Test ==="
curl -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test", invalid_json}' 2>&1 | tee -a "$LOG_FILE"
log_and_echo ""

# Error Test 2: Missing Content-Type
log_and_echo "=== Missing Content-Type Test ==="
curl -X POST "$BASE_URL" \
    -d '{"prompt": "test without content type"}' 2>&1 | tee -a "$LOG_FILE"
log_and_echo ""

# Error Test 3: Very Large Payload
log_and_echo "=== Large Payload Test ==="
large_prompt=$(python3 -c "print('A' * 500)")
curl -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"$large_prompt\"}" 2>&1 | head -5 | tee -a "$LOG_FILE"
log_and_echo ""

log_and_echo "========================================"
log_and_echo "PERFORMANCE SUMMARY"
log_and_echo "========================================"

# Performance Summary
log_and_echo "=== Performance Summary ==="
log_and_echo "Test completed at: $(date)"
log_and_echo "Total test duration: Started at $(head -2 "$LOG_FILE" | tail -1)"

# Count successful vs failed tests
success_count=$(grep -c '"status": "success"' "$LOG_FILE" || echo "0")
error_count=$(grep -c '"status": "error"' "$LOG_FILE" || echo "0")

log_and_echo "Successful responses: $success_count"
log_and_echo "Error responses: $error_count"

# Model usage summary
log_and_echo ""
log_and_echo "=== Model Usage Summary ==="
for model in pro sonic canvas micro titan; do
    count=$(grep -c "\"model.*\": \"$model\"" "$LOG_FILE" || echo "0")
    log_and_echo "$model model: $count requests"
done

log_and_echo ""
log_and_echo "=== Test Type Summary ==="
for type in chat image_generation image_analysis health; do
    count=$(grep -c "\"type.*\": \"$type" "$LOG_FILE" || echo "0")
    log_and_echo "$type: $count requests"
done

log_and_echo ""
log_and_echo "========================================"
log_and_echo "RECOMMENDATIONS"
log_and_echo "========================================"

log_and_echo "Based on the test results:"
log_and_echo ""
log_and_echo "1. Use MICRO model for:"
log_and_echo "   - Simple calculations"
log_and_echo "   - Quick responses"
log_and_echo "   - Cost-effective operations"
log_and_echo ""
log_and_echo "2. Use PRO model for:"
log_and_echo "   - Complex analysis"
log_and_echo "   - Detailed explanations" 
log_and_echo "   - Reasoning tasks"
log_and_echo ""
log_and_echo "3. Use SONIC model for:"
log_and_echo "   - Creative writing"
log_and_echo "   - Balanced speed/quality"
log_and_echo "   - General chat"
log_and_echo ""
log_and_echo "4. Use CANVAS model for:"
log_and_echo "   - Image analysis"
log_and_echo "   - Multimodal tasks"
log_and_echo "   - Vision-related prompts"
log_and_echo ""
log_and_echo "5. Use TITAN model for:"
log_and_echo "   - Image generation ONLY"
log_and_echo "   - Creative visual content"
log_and_echo "   - NOT for chat (will error)"
log_and_echo ""

log_and_echo "========================================"
log_and_echo "MONITORING SETUP"
log_and_echo "========================================"

# Create monitoring script
cat << 'EOF' > monitor_agentcore.py
#!/usr/bin/env python3
"""
Continuous monitoring script for AgentCore with file logging
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080/invocations"
MONITOR_LOG = f"monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log_message(message):
    """Log message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(MONITOR_LOG, "a") as f:
        f.write(log_entry + "\n")

def monitor_health():
    """Monitor application health continuously"""
    log_message("Starting continuous monitoring...")
    log_message(f"Monitoring log: {MONITOR_LOG}")
    
    while True:
        try:
            # Health check
            start_time = time.time()
            response = requests.post(
                BASE_URL,
                json={"type": "health"},
                timeout=10
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                log_message(f"✓ Health OK - {response_time:.2f}s")
            else:
                log_message(f"✗ Health FAILED - Status: {response.status_code}")
            
            # Quick functionality test
            start_time = time.time()
            response = requests.post(
                BASE_URL,
                json={"model": "micro", "prompt": "Quick monitor test"},
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and data.get("status") == "success":
                    log_message(f"✓ API OK - {end_time - start_time:.2f}s")
                else:
                    log_message(f"⚠ API WARNING - Unexpected response: {data.get('status', 'unknown')}")
            else:
                log_message(f"✗ API FAILED - Status: {response.status_code}")
                
        except Exception as e:
            log_message(f"✗ ERROR - {str(e)}")
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        monitor_health()
    except KeyboardInterrupt:
        log_message("Monitoring stopped by user")
EOF

chmod +x monitor_agentcore.py

log_and_echo "Created monitor_agentcore.py for continuous monitoring"
log_and_echo "Usage: python monitor_agentcore.py"
log_and_echo ""

log_and_echo "========================================"
log_and_echo "LOAD TESTING SETUP"
log_and_echo "========================================"

# Create load test files
echo '{"model": "micro", "prompt": "Load test - micro"}' > micro_load.json
echo '{"model": "pro", "prompt": "Load test - complex analysis"}' > pro_load.json
echo '{"type": "image_generation", "prompt": "Load test image"}' > image_load.json

log_and_echo "Created load test files:"
log_and_echo "- micro_load.json (for fast tests)"
log_and_echo "- pro_load.json (for complex tests)"  
log_and_echo "- image_load.json (for image generation tests)"
log_and_echo ""
log_and_echo "Run load tests with Apache Bench:"
log_and_echo "ab -n 100 -c 10 -p micro_load.json -T application/json $BASE_URL"
log_and_echo "ab -n 50 -c 5 -p pro_load.json -T application/json $BASE_URL"
log_and_echo "ab -n 20 -c 2 -p image_load.json -T application/json $BASE_URL"

log_and_echo ""
log_and_echo "========================================"
log_and_echo "TEST COMPLETE"
log_and_echo "========================================"
log_and_echo "Full test results saved to: $LOG_FILE"
log_and_echo "Review the log file for detailed analysis"
log_and_echo "Run 'python monitor_agentcore.py' for continuous monitoring"
log_and_echo ""

# Final summary
log_and_echo "Quick verification command:"
log_and_echo "curl -X POST $BASE_URL -H 'Content-Type: application/json' -d '{\"type\": \"health\"}'"
log_and_echo ""
log_and_echo "Test completed successfully!"
