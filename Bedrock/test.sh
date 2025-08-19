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
    -H "Content-Type
