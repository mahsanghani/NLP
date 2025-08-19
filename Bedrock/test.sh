# UPDATED CURL COMMANDS FOR BEDROCK AGENTCORE
# These commands should work with the fixed application

# First, make sure your application is running
# python your_app.py

# 1. Health Check (GET request)
echo "=== 1. Health Check ==="
curl -X GET http://localhost:8080/health
echo -e "\n"

# 2. Health Check (POST request - some frameworks expect POST)
echo "=== 2. Health Check (POST) ==="
curl -X POST http://localhost:8080/health \
  -H "Content-Type: application/json" \
  -d '{}'
echo -e "\n"

# 3. Root endpoint (same as entrypoint)
echo "=== 3. Root Endpoint ==="
curl -X POST http://localhost:8080/ \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you today?"}'
echo -e "\n"

# 4. Main entrypoint with default model
echo "=== 4. Main Entrypoint (Default) ==="
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me a short joke"}'
echo -e "\n"

# 5. Test Nova Pro Model
echo "=== 5. Nova Pro Model ==="
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "pro",
    "prompt": "Explain artificial intelligence in 2 sentences"
  }'
echo -e "\n"

# 6. Test Nova Micro Model (Fast responses)
echo "=== 6. Nova Micro Model ==="
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "micro",
    "prompt": "What is 25 * 4?"
  }'
echo -e "\n"

# 7. Test Nova Sonic Model
echo "=== 7. Nova Sonic Model ==="
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonic",
    "prompt": "Write a haiku about clouds"
  }'
echo -e "\n"

# 8. Chat route with Pro model
echo "=== 8. Chat Route (Pro) ==="
curl -X POST "http://localhost:8080/chat/pro" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are the benefits of renewable energy?"}'
echo -e "\n"

# 9. Chat route with Micro model
echo "=== 9. Chat Route (Micro) ==="
curl -X POST "http://localhost:8080/chat/micro" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello there!"}'
echo -e "\n"

# 10. Chat route with invalid model (should return error)
echo "=== 10. Invalid Model Test ==="
curl -X POST "http://localhost:8080/chat/invalid_model" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "This should fail gracefully"}'
echo -e "\n"

# 11. Basic Image Generation
echo "=== 11. Basic Image Generation ==="
curl -X POST http://localhost:8080/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A serene mountain landscape at sunset"
  }'
echo -e "\n"

# 12. Image Generation with Parameters
echo "=== 12. Image Generation with Parameters ==="
curl -X POST http://localhost:8080/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic city with flying cars",
    "image_params": {
      "width": 512,
      "height": 512,
      "cfg_scale": 8.0,
      "number_of_images": 1,
      "seed": 12345
    }
  }'
echo -e "\n"

# 13. Image Analysis without image (should error)
echo "=== 13. Image Analysis (No Image) ==="
curl -X POST http://localhost:8080/analyze-image \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What do you see in this image?"
  }'
echo -e "\n"

# 14. Image Analysis with test image
echo "=== 14. Image Analysis (With Image) ==="
curl -X POST http://localhost:8080/analyze-image \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Describe this image",
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "image_format": "png"
  }'
echo -e "\n"

# 15. Test with empty payload
echo "=== 15. Empty Payload Test ==="
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{}'
echo -e "\n"

# 16. Test with only prompt (no model specified)
echo "=== 16. No Model Specified ==="
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "This should use the default model"
  }'
echo -e "\n"

# 17. Test Canvas model directly
echo "=== 17. Canvas Model Test ==="
curl -X POST "http://localhost:8080/chat/canvas" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a description of a beautiful garden"}'
echo -e "\n"

# 18. Test Titan model directly
echo "=== 18. Titan Model Test ==="
curl -X POST "http://localhost:8080/chat/titan" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Generate an image of a robot"}'
echo -e "\n"

# 19. Test route that doesn't exist (should return 404 info)
echo "=== 19. Non-existent Route ==="
curl -X POST "http://localhost:8080/nonexistent" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
echo -e "\n"

# 20. Large prompt test
echo "=== 20. Large Prompt Test ==="
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "pro",
    "prompt": "Please provide a comprehensive overview of machine learning, including supervised learning, unsupervised learning, reinforcement learning, deep learning, neural networks, and their real-world applications in various industries such as healthcare, finance, transportation, and technology."
  }'
echo -e "\n"

echo "=== All tests completed! ==="

# DEBUGGING COMMANDS
# If you're still getting errors, try these debugging commands:

echo "=== DEBUGGING COMMANDS ==="

# Check if the server is running
echo "--- Server Status ---"
curl -I http://localhost:8080/health 2>/dev/null | head -1 || echo "Server not responding"

# Test with verbose output
echo "--- Verbose Test ---"
curl -v -X POST http://localhost:8080/health \
  -H "Content-Type: application/json" \
  -d '{}'

# Test with different content type
echo "--- Different Content Type ---"
curl -X POST http://localhost:8080 \
  -H "Content-Type: text/plain" \
  -d "test message"

# LOAD TESTING COMMANDS
echo "=== LOAD TESTING ==="

# Create test files for load testing
echo '{"prompt": "Load test message"}' > load_test.json
echo '{"model": "micro", "prompt": "Quick test"}' > micro_test.json

# Simple load test (requires apache bench)
# ab -n 10 -c 2 -p load_test.json -T application/json http://localhost:8080/

# Concurrent requests using background processes
echo "--- Concurrent Test ---"
for i in {1..5}; do
  curl -X POST http://localhost:8080 \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"micro\", \"prompt\": \"Concurrent test $i\"}" &
done
wait

echo "=== Testing completed! ==="

# MONITORING SCRIPT
# Save this as monitor.sh and run it in a separate terminal
cat << 'EOF' > monitor.sh
#!/bin/bash
echo "Starting continuous monitoring..."
while true; do
  echo "=== $(date) ==="
  
  # Health check
  response=$(curl -s -X GET http://localhost:8080/health)
  echo "Health: $response"
  
  # Simple test
  response=$(curl -s -X POST http://localhost:8080 \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Monitor test"}')
  echo "API Test: ${response:0:100}..."
  
  echo "---"
  sleep 30
done
EOF

chmod +x monitor.sh
echo "Monitor script created. Run with: ./monitor.sh"

# ERROR ANALYSIS
echo "=== COMMON ERROR SOLUTIONS ==="
echo "1. '404 Not Found' - Check if server is running on correct port"
echo "2. 'Connection refused' - Server not started or wrong port"
echo "3. 'dict object is not callable' - Agent invocation issue, check logs"
echo "4. JSON decode errors - Check payload format"
echo "5. Model errors - Check AWS credentials and model availability"

echo ""
echo "To start the server:"
echo "python your_app.py"
echo ""
echo "To check server logs:"
echo "tail -f your_app.log"  # if logging to file
echo ""
echo "To check if port 8080 is in use:"
echo "netstat -tlnp | grep :8080"
echo "lsof -i :8080"
