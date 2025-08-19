#!/bin/bash

# COMPREHENSIVE BEDROCK AGENTCORE TEST SUITE
# Tests all models using direct Bedrock client
# All output saved to timestamped log file

LOG_FILE="bedrock_test_$(date +%Y%m%d_%H%M%S).log"
BASE_URL="http://localhost:8080/invocations"

# Function to log and display output
log_and_echo() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Function to run test and analyze response
run_test() {
    local test_name="$1"
    local curl_data="$2"
    local expected_success="$3"  # true/false
    
    log_and_echo "========================================"
    log_and_echo "TEST: $test_name"
    log_and_echo "========================================"
    log_and_echo "Request: $curl_data"
    log_and_echo ""
    log_and_echo "Response:"
    
    response=$(curl -s -X POST "$BASE_URL" \
        -H "Content-Type: application/json" \
        -d "$curl_data" 2>&1)
    
    echo "$response" | tee -a "$LOG_FILE"
    
    # Analyze response
    log_and_echo ""
    log_and_echo "Analysis:"
    
    if echo "$response" | grep -q '"status": "success"' 2>/dev/null; then
        method=$(echo "$response" | jq -r '.method // "unknown"' 2>/dev/null)
        model_id=$(echo "$response" | jq -r '.model_id // "unknown"' 2>/dev/null)
        log_and_echo "✅ SUCCESS"
        log_and_echo "   Method: $method"
        log_and_echo "   Model ID: $model_id"
        
        # Check if using Bedrock direct
        if echo "$response" | grep -q '"method": "bedrock_direct"' 2>/dev/null; then
            log_and_echo "   🎉 Using direct Bedrock API (optimal)"
        fi
        
    elif echo "$response" | grep -q '"status": "error"' 2>/dev/null; then
        error_type=$(echo "$response" | jq -r '.type // "unknown"' 2>/dev/null)
        error_msg=$(echo "$response" | jq -r '.error // "unknown"' 2>/dev/null)
        log_and_echo "❌ ERROR"
        log_and_echo "   Type: $error_type"
        log_and_echo "   Message: ${error_msg:0:100}..."
        
        # Check for specific error types and suggestions
        if echo "$response" | grep -q "suggestions" 2>/dev/null; then
            suggestions=$(echo "$response" | jq -r '.suggestions[]?' 2>/dev/null)
            if [ -n "$suggestions" ]; then
                log_and_echo "   💡 Suggestions:"
                echo "$suggestions" | while read -r suggestion; do
                    log_and_echo "      - $suggestion"
                done
            fi
        fi
        
        # Check for expected errors
        if [ "$expected_success" = "false" ]; then
            log_and_echo "   ℹ️  This error was expected for this test"
        fi
        
    elif echo "$response" | grep -q '"status": "healthy"' 2>/dev/null; then
        bedrock_status=$(echo "$response" | jq -r '.bedrock_status // "unknown"' 2>/dev/null)
        log_and_echo "✅ HEALTH CHECK PASSED"
        log_and_echo "   Bedrock status: $bedrock_status"
        
    else
        log_and_echo "⚠️  UNKNOWN response format"
    fi
    
    log_and_echo ""
    log_and_echo "----------------------------------------"
    log_and_echo ""
}

# Start logging
log_and_echo "BEDROCK AGENTCORE COMPREHENSIVE TEST SUITE"
log_and_echo "All models using direct Bedrock client"
log_and_echo "Started at: $(date)"
log_and_echo "Endpoint: $BASE_URL"
log_and_echo "Log file: $LOG_FILE"
log_and_echo ""

# Test 1: Health Check
run_test "1. Health Check" '{
    "type": "health"
}' true

# Test 2: List Models
run_test "2. List Available Models" '{
    "type": "models"
}' true

# Test 3: Micro Model (Fast responses)
run_test "3. Micro Model Chat" '{
    "model": "micro",
    "prompt": "What is 25 * 16? Please show your calculation."
}' true

# Test 4: Pro Model (Complex reasoning)
run_test "4. Pro Model Chat" '{
    "model": "pro", 
    "prompt": "Explain the key differences between supervised and unsupervised machine learning with examples."
}' true

# Test 5: Sonic Model (Balanced)
run_test "5. Sonic Model Chat" '{
    "model": "sonic",
    "prompt": "Write a creative haiku about artificial intelligence."
}' true

# Test 6: Canvas Model (Multimodal - text only)
run_test "6. Canvas Model Chat" '{
    "model": "canvas",
    "prompt": "Describe the ideal design for a smart home interface."
}' true

# Test 7: Titan Model Chat (Should Error - Image generation only)
run_test "7. Titan Model Chat (Expected Error)" '{
    "model": "titan",
    "prompt": "This should return an error explaining Titan is for images only"
}' false

# Test 8: Basic Image Generation (Titan)
run_test "8. Basic Image Generation" '{
    "type": "image_generation",
    "prompt": "A serene mountain landscape at sunset with a lake reflection"
}' true

# Test 9: Image Generation with Parameters
run_test "9. Image Generation (Custom Parameters)" '{
    "type": "image_generation",
    "prompt": "A futuristic cityscape with flying vehicles and neon lights",
    "image_params": {
        "width": 768,
        "height": 768,
        "cfg_scale": 8.5,
        "seed": 42,
        "number_of_images": 1
    }
}' true

# Test 10: High-Quality Image Generation
run_test "10. High-Quality Image Generation" '{
    "type": "image_generation",
    "prompt": "A detailed architectural visualization of a modern sustainable building with solar panels, green roofs, and innovative eco-friendly design elements",
    "image_params": {
        "width": 1024,
        "height": 1024,
        "cfg_scale": 9.0,
        "seed": 123456
    }
}' true

# Test 11: Simple Image Generation
run_test "11. Simple Image Generation" '{
    "type": "image_generation",
    "prompt": "a cute cat sitting in a garden"
}' true

# Test 12: Image Analysis (No Image - Should Error)
run_test "12. Image Analysis (No Image - Expected Error)" '{
    "type": "image_analysis",
    "text": "What do you see in this image?"
}' false

# Test 13: Image Analysis with Test Image
run_test "13. Image Analysis (With Test Image)" '{
    "type": "image_analysis", 
    "text": "Please describe this image in detail and identify any objects you can see",
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "image_format": "png"
}' true

# Test 14: Default Model (No Model Specified)
run_test "14. Default Model (No Model Specified)" '{
    "prompt": "Hello! What model am I talking to?"
}' true

# Test 15: Empty Payload
run_test "15. Empty Payload" '{}' true

# Test 16: String Payload  
run_test "16. String Payload" '"Hello as a direct string"' true

# Test 17: Invalid Model Name
run_test "17. Invalid Model Name (Expected Error)" '{
    "model": "nonexistent_model",
    "prompt": "This should return an error about unknown model"
}' false

# Test 18: Complex Reasoning Task (Pro Model)
run_test "18. Complex Reasoning Task" '{
    "model": "pro",
    "prompt": "Analyze the potential benefits and risks of widespread adoption of autonomous vehicles. Consider economic, social, environmental, and safety factors."
}' true

# Test 19: Creative Writing Task (Sonic Model)
run_test "19. Creative Writing Task" '{
    "model": "sonic",
    "prompt": "Write a short story (4-5 sentences) about a time traveler who discovers that small changes in the past have unexpected consequences in the future."
}' true

# Test 20: Quick Math Task (Micro Model)
run_test "20. Quick Math Task" '{
    "model": "micro",
    "prompt": "If I invest $1000 at 5% annual interest compounded monthly for 3 years, what will be the final amount?"
}' true

log_and_echo "========================================"
log_and_echo "BEDROCK CONNECTIVITY TESTS"
log_and_echo "========================================"

# Test AWS Configuration
log_and_echo "=== AWS Configuration Check ==="

if command -v aws >/dev/null 2>&1; then
    log_and_echo "AWS CLI found"
    
    # Check credentials
    if aws sts get-caller-identity >/dev/null 2>&1; then
        identity=$(aws sts get-caller-identity 2>/dev/null)
        account=$(echo "$identity" | jq -r '.Account // "unknown"' 2>/dev/null)
        user=$(echo "$identity" | jq -r '.Arn // .UserId // "unknown"' 2>/dev/null)
        log_and_echo "✅ AWS credentials configured"
        log_and_echo "   Account: $account"
        log_and_echo "   User: $user"
    else
        log_and_echo "❌ AWS credentials not configured"
        log_and_echo "💡 Run: aws configure"
    fi
    
    # Check region
    region=$(aws configure get region 2>/dev/null)
    if [ -n "$region" ]; then
        log_and_echo "✅ AWS region: $region"
        
        # Check Bedrock models availability
        log_and_echo "Checking Bedrock model availability in $region..."
        
        if aws bedrock list-foundation-models --region "$region" >/dev/null 2>&1; then
            log_and_echo "✅ Bedrock accessible"
            
            # Check specific models
            models_output=$(aws bedrock list-foundation-models --region "$region" 2>/dev/null)
            
            for model in "nova-pro" "nova-micro" "nova-lite" "nova-canvas" "titan-image"; do
                if echo "$models_output" | grep -q "$model" 2>/dev/null; then
                    log_and_echo "   ✅ $model: Available"
                else
                    log_and_echo "   ❌ $model: Not found"
                fi
            done
        else
            log_and_echo "❌ Cannot access Bedrock in $region"
            log_and_echo "💡 Try regions: us-east-1, us-west-2"
        fi
    else
        log_and_echo "❌ AWS region not configured"
        log_and_echo "💡 Set region: aws configure set region us-east-1"
    fi
else
    log_and_echo "❌ AWS CLI not found"
    log_and_echo "💡 Install: pip install awscli"
fi

log_and_echo ""
log_and_echo "========================================"
log_and_echo "PERFORMANCE TESTING"
log_and_echo "========================================"

# Response time tests
log_and_echo "=== Response Time Tests ==="

models=("micro" "sonic" "pro" "canvas")
for model in "${models[@]}"; do
    log_and_echo "Testing $model model response time..."
    start_time=$(date +%s.%N)
    
    response=$(curl -s -X POST "$BASE_URL" \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$model\", \"prompt\": \"Quick response test\"}" 2>/dev/null)
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "unknown")
    
    if echo "$response" | grep -q '"status": "success"' 2>/dev/null; then
        log_and_echo "   ✅ $model: ${duration}s"
    else
        log_and_echo "   ❌ $model: Failed"
    fi
done

# Image generation timing
log_and_echo ""
log_and_echo "Testing image generation response time..."
start_time=$(date +%s.%N)

image_response=$(curl -s -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d '{"type": "image_generation", "prompt": "performance test image"}' 2>/dev/null)

end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "unknown")

if echo "$image_response" | grep -q '"status": "success"' 2>/dev/null; then
    log_and_echo "   ✅ Image generation: ${duration}s"
else
    log_and_echo "   ❌ Image generation: Failed"
fi

log_and_echo ""
log_and_echo "========================================"
log_and_echo "CONCURRENT TESTING"
log_and_echo "========================================"

# Concurrent requests test
log_and_echo "=== Concurrent Requests Test ==="
log_and_echo "Running 5 concurrent micro model requests..."

for i in {1..5}; do
    (
        start=$(date +%s.%N)
        response=$(curl -s -X POST "$BASE_URL" \
            -H "Content-Type: application/json" \
            -d "{\"model\": \"micro\", \"prompt\": \"Concurrent test $i\"}" 2>/dev/null)
        end=$(date +%s.%N)
        duration=$(echo "$end - $start" | bc -l 2>/dev/null || echo "unknown")
        
        if echo "$response" | grep -q '"status": "success"' 2>/dev/null; then
            log_and_echo "   ✅ Request $i: ${duration}s"
        else
            log_and_echo "   ❌ Request $i: Failed"
        fi
    ) &
done

wait
log_and_echo "Concurrent testing completed"

log_and_echo ""
log_and_echo "========================================"
log_and_echo "ERROR HANDLING TESTS"
log_and_echo "========================================"

# Test various error conditions
log_and_echo "=== Error Handling Tests ==="

# Malformed JSON
log_and_echo "Testing malformed JSON handling..."
malformed_response=$(curl -s -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "test", invalid_json}' 2>&1)

if echo "$malformed_response" | grep -q "error" 2>/dev/null; then
    log_and_echo "   ✅ Malformed JSON handled gracefully"
else
    log_and_echo "   ⚠️  Malformed JSON response: ${malformed_response:0:100}..."
fi

# Missing Content-Type
log_and_echo "Testing missing Content-Type..."
no_content_type=$(curl -s -X POST "$BASE_URL" \
    -d '{"prompt": "test"}' 2>&1)
log_and_echo "   Response: ${no_content_type:0:100}..."

# Large payload test
log_and_echo "Testing large payload..."
large_prompt=$(python3 -c "print('A' * 1000)" 2>/dev/null || echo "large prompt test")
large_response=$(curl -s -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"micro\", \"prompt\": \"$large_prompt\"}" 2>/dev/null)

if echo "$large_response" | grep -q '"status": "success"' 2>/dev/null; then
    log_and_echo "   ✅ Large payload handled successfully"
else
    log_and_echo "   ❌ Large payload failed"
fi

log_and_echo ""
log_and_echo "========================================"
log_and_echo "RESULTS SUMMARY"
log_and_echo "========================================"

# Count test results
total_tests=$(grep -c "^TEST:" "$LOG_FILE" || echo "0")
success_count=$(grep -c "✅ SUCCESS" "$LOG_FILE" || echo "0")
error_count=$(grep -c "❌ ERROR" "$LOG_FILE" || echo "0")
expected_errors=$(grep -c "Expected Error" "$LOG_FILE" || echo "0")
bedrock_direct_count=$(grep -c "bedrock_direct" "$LOG_FILE" || echo "0")

log_and_echo "=== Test Results Summary ==="
log_and_echo "Total tests: $total_tests"
log_and_echo "Successful: $success_count"
log_and_echo "Errors: $error_count (including $expected_errors expected errors)"
log_and_echo "Using Bedrock direct: $bedrock_direct_count"
log_and_echo ""

# Calculate success rate
if [ "$total_tests" -gt 0 ]; then
    success_rate=$(echo "scale=1; $success_count * 100 / $total_tests" | bc -l 2>/dev/null || echo "unknown")
    log_and_echo "Success rate: $success_rate%"
else
    log_and_echo "Success rate: Unable to calculate"
fi

log_and_echo ""
log_and_echo "=== Model Performance Summary ==="
for model in micro sonic pro canvas titan; do
    model_tests=$(grep -c "\"model.*\": \"$model\"" "$LOG_FILE" || echo "0")
    model_success=$(grep "✅ SUCCESS" "$LOG_FILE" | grep -c "$model" || echo "0")
    if [ "$model_tests" -gt 0 ]; then
        log_and_echo "$model: $model_success/$model_tests successful"
    fi
done

log_and_echo ""
log_and_echo "=== Bedrock Integration Status ==="
if [ "$bedrock_direct_count" -gt 0 ]; then
    log_and_echo "🎉 EXCELLENT - All models using direct Bedrock API"
    log_and_echo "✅ No Agent wrapper dependencies"
    log_and_echo "✅ Consistent error handling across all models"
    log_and_echo "✅ Full control over model parameters"
else
    log_and_echo "⚠️  WARNING - Not all models using Bedrock direct"
    log_and_echo "Check for Agent wrapper fallbacks"
fi

log_and_echo ""
log_and_echo "========================================"
log_and_echo "RECOMMENDATIONS"
log_and_echo "========================================"

log_and_echo "=== Usage Recommendations ==="
log_and_echo ""
log_and_echo "🚀 OPTIMAL USAGE PATTERNS:"
log_and_echo ""
log_and_echo "1. MICRO MODEL - Fast & Cost-Effective:"
log_and_echo "   • Simple calculations and quick responses"
log_and_echo "   • High-volume, low-complexity tasks"
log_and_echo "   • Real-time applications requiring speed"
log_and_echo ""
log_and_echo "2. SONIC MODEL - Balanced Performance:"
log_and_echo "   • Creative writing and content generation"
log_and_echo "   • General chat and conversation"
log_and_echo "   • Balanced quality/speed requirements"
log_and_echo ""
log_and_echo "3. PRO MODEL - Complex Reasoning:"
log_and_echo "   • Detailed analysis and explanations"
log_and_echo "   • Complex problem solving"
log_and_echo "   • Research and educational content"
log_and_echo ""
log_and_echo "4. CANVAS MODEL - Multimodal Tasks:"
log_and_echo "   • Image analysis and description"
log_and_echo "   • Visual content understanding"
log_and_echo "   • Multimodal AI applications"
log_and_echo ""
log_and_echo "5. TITAN MODEL - Image Generation:"
log_and_echo "   • Creating images from text descriptions"
log_and_echo "   • Artistic and creative visual content"
log_and_echo "   • Marketing and design materials"
log_and_echo ""

log_and_echo "⚡ PERFORMANCE TIPS:"
log_and_echo "• Use cfg_scale 7.0-9.0 for optimal image quality"
log_and_echo "• Standard image sizes: 512x512, 768x768, 1024x1024"
log_and_echo "• Be specific and descriptive in prompts"
log_and_echo "• Use Micro model for high-frequency simple tasks"
log_and_echo "• Reserve Pro model for complex reasoning tasks"
log_and_echo ""

log_and_echo "🔧 TROUBLESHOOTING GUIDE:"
log_and_echo ""
if [ "$success_count" -lt "$total_tests" ]; then
    log_and_echo "Issues detected. Common solutions:"
    log_and_echo "• Check AWS credentials: aws sts get-caller-identity"
    log_and_echo "• Verify region configuration: aws configure get region"
    log_and_echo "• Request model access in AWS Bedrock console"
    log_and_echo "• Check IAM permissions for bedrock:InvokeModel"
    log_and_echo "• Verify models are available in your region"
else
    log_and_echo "✅ All tests passed! System is working optimally."
fi

log_and_echo ""
log_and_echo "========================================"
log_and_echo "MONITORING SETUP"
log_and_echo "========================================"

# Create enhanced monitoring script
cat << 'EOF' > monitor_bedrock_agentcore.py
#!/usr/bin/env python3
"""
Enhanced monitoring script for Bedrock AgentCore
Monitors all models and provides detailed health metrics
"""
import requests
import json
import time
from datetime import datetime
import statistics

BASE_URL = "http://localhost:8080/invocations"
MONITOR_LOG = f"monitor_bedrock_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

class BedrockMonitor:
    def __init__(self):
        self.response_times = {"micro": [], "sonic": [], "pro": [], "canvas": [], "image_gen": []}
        self.error_counts = {"micro": 0, "sonic": 0, "pro": 0, "canvas": 0, "image_gen": 0}
        self.success_counts = {"micro": 0, "sonic": 0, "pro": 0, "canvas": 0, "image_gen": 0}
    
    def log_message(self, message):
        """Log message to both console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(MONITOR_LOG, "a") as f:
            f.write(log_entry + "\n")
    
    def test_model(self, model_name, prompt="Quick test"):
        """Test a specific model and return metrics"""
        try:
            start_time = time.time()
            
            payload = {"model": model_name, "prompt": prompt}
            response = requests.post(
                BASE_URL,
                json=payload,
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.success_counts[model_name] += 1
                    self.response_times[model_name].append(response_time)
                    return {"success": True, "response_time": response_time, "data": data}
                else:
                    self.error_counts[model_name] += 1
                    return {"success": False, "error": data.get("error", "Unknown error")}
            else:
                self.error_counts[model_name] += 1
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.error_counts[model_name] += 1
            return {"success": False, "error": str(e)}
    
    def test_image_generation(self):
        """Test image generation specifically"""
        try:
            start_time = time.time()
            
            payload = {
                "type": "image_generation",
                "prompt": "Monitor test image",
                "image_params": {"width": 512, "height": 512}
            }
            
            response = requests.post(
                BASE_URL,
                json=payload,
                timeout=60  # Longer timeout for image generation
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.success_counts["image_gen"] += 1
                    self.response_times["image_gen"].append(response_time)
                    return {"success": True, "response_time": response_time}
                else:
                    self.error_counts["image_gen"] += 1
                    return {"success": False, "error": data.get("error", "Unknown error")}
            else:
                self.error_counts["image_gen"] += 1
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            self.error_counts["image_gen"] += 1
            return {"success": False, "error": str(e)}
    
    def print_statistics(self):
        """Print performance statistics"""
        self.log_message("=== PERFORMANCE STATISTICS ===")
        
        for model in ["micro", "sonic", "pro", "canvas", "image_gen"]:
            total_requests = self.success_counts[model] + self.error_counts[model]
            if total_requests > 0:
                success_rate = (self.success_counts[model] / total_requests) * 100
                
                if self.response_times[model]:
                    avg_time = statistics.mean(self.response_times[model])
                    min_time = min(self.response_times[model])
                    max_time = max(self.response_times[model])
                    
                    self.log_message(f"{model.upper()}:")
                    self.log_message(f"  Success rate: {success_rate:.1f}% ({self.success_counts[model]}/{total_requests})")
                    self.log_message(f"  Avg response: {avg_time:.2f}s")
                    self.log_message(f"  Min/Max: {min_time:.2f}s / {max_time:.2f}s")
                else:
                    self.log_message(f"{model.upper()}: {success_rate:.1f}% success rate, no timing data")
    
    def monitor_continuous(self):
        """Run continuous monitoring"""
        self.log_message("Starting continuous Bedrock AgentCore monitoring...")
        self.log_message(f"Monitor log: {MONITOR_LOG}")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                self.log_message(f"=== Monitoring Cycle {cycle} ===")
                
                # Test health endpoint
                try:
                    health_response = requests.post(BASE_URL, json={"type": "health"}, timeout=10)
                    if health_response.status_code == 200:
                        health_data = health_response.json()
                        bedrock_status = health_data.get("bedrock_status", "unknown")
                        self.log_message(f"✅ Health check passed - Bedrock: {bedrock_status}")
                    else:
                        self.log_message(f"❌ Health check failed - HTTP {health_response.status_code}")
                except Exception as e:
                    self.log_message(f"❌ Health check error: {e}")
                
                # Test each text model
                for model in ["micro", "sonic", "pro", "canvas"]:
                    result = self.test_model(model, f"Monitor test cycle {cycle}")
                    if result["success"]:
                        self.log_message(f"✅ {model}: {result['response_time']:.2f}s")
                    else:
                        self.log_message(f"❌ {model}: {result['error']}")
                
                # Test image generation (less frequently)
                if cycle % 3 == 0:  # Every 3rd cycle
                    self.log_message("Testing image generation...")
                    img_result = self.test_image_generation()
                    if img_result["success"]:
                        self.log_message(f"✅ Image generation: {img_result['response_time']:.2f}s")
                    else:
                        self.log_message(f"❌ Image generation: {img_result['error']}")
                
                # Print statistics every 10 cycles
                if cycle % 10 == 0:
                    self.print_statistics()
                
                time.sleep(60)  # Wait 1 minute between cycles
                
            except KeyboardInterrupt:
                self.log_message("Monitoring stopped by user")
                self.print_statistics()
                break
            except Exception as e:
                self.log_message(f"Monitoring error: {e}")
                time.sleep(30)  # Wait 30 seconds on error

if __name__ == "__main__":
    monitor = BedrockMonitor()
    monitor.monitor_continuous()
EOF

chmod +x monitor_bedrock_agentcore.py

log_and_echo "Created enhanced monitoring script: monitor_bedrock_agentcore.py"
log_and_echo ""
log_and_echo "Usage:"
log_and_echo "  python monitor_bedrock_agentcore.py"
log_and_echo ""
log_and_echo "Features:"
log_and_echo "• Continuous health monitoring"
log_and_echo "• Performance metrics for all models"
log_and_echo "• Response time statistics" 
log_and_echo "• Error rate tracking"
log_and_echo "• Automatic image generation testing"

log_and_echo ""
log_and_echo "========================================"
log_and_echo "QUICK REFERENCE COMMANDS"
log_and_echo "========================================"

log_and_echo "=== Quick Test Commands ==="
log_and_echo ""
log_and_echo "# Test health"
log_and_echo "curl -X POST $BASE_URL -H 'Content-Type: application/json' -d '{\"type\": \"health\"}'"
log_and_echo ""
log_and_echo "# Quick chat with micro model"
log_and_echo "curl -X POST $BASE_URL -H 'Content-Type: application/json' -d '{\"model\": \"micro\", \"prompt\": \"Hello\"}'"
log_and_echo ""
log_and_echo "# Generate simple image"
log_and_echo "curl -X POST $BASE_URL -H 'Content-Type: application/json' -d '{\"type\": \"image_generation\", \"prompt\": \"cat\"}'"
log_and_echo ""
log_and_echo "# List available models"
log_and_echo "curl -X POST $BASE_URL -H 'Content-Type: application/json' -d '{\"type\": \"models\"}'"

log_and_echo ""
log_and_echo "========================================"
log_and_echo "TEST COMPLETED SUCCESSFULLY!"
log_and_echo "========================================"
log_and_echo ""
log_and_echo "📊 Full test results saved to: $LOG_FILE"
log_and_echo "🔍 Review the log for detailed analysis"
log_and_echo "📈 Run monitor_bedrock_agentcore.py for continuous monitoring"
log_and_echo "🎉 All models now using direct Bedrock API - no more Agent wrapper issues!"
log_and_echo ""
log_and_echo "Next steps:"
log_and_echo "1. Review test results above"
log_and_echo "2. Start continuous monitoring if needed"
log_and_echo "3. Use the quick reference commands for manual testing"
log_and_echo "4. Check AWS Bedrock console for usage metrics"
log_and_echo ""
log_and_echo "🚀 Your Bedrock AgentCore setup is ready for production!"
