# 1. Health Check
curl -X GET http://localhost:8080/health

# 2. Basic Entrypoint Test
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you today?"}'

# 3. Test Nova Pro Model
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "pro",
    "prompt": "Explain the theory of relativity in simple terms"
  }'

# 4. Test Nova Micro Model (Fast, Cost-effective)
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "micro",
    "prompt": "What is 15 * 23?"
  }'

# 5. Test Nova Sonic Model
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonic",
    "prompt": "Write a haiku about technology"
  }'

# 6. Chat Route with Specific Model
curl -X POST http://localhost:8080/chat/pro \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me about machine learning"}'

# 7. Chat Route with Invalid Model (Error Test)
curl -X POST http://localhost:8080/chat/invalid_model \
  -H "Content-Type: application/json" \
  -d '{"prompt": "This should fail"}'

# 8. Basic Image Generation with Titan
curl -X POST http://localhost:8080/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains with a lake"
  }'

# 9. Image Generation with Custom Parameters
curl -X POST http://localhost:8080/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cyberpunk city with neon lights",
    "image_params": {
      "width": 768,
      "height": 768,
      "cfg_scale": 7.5,
      "number_of_images": 1,
      "seed": 12345
    }
  }'

# 10. Image Analysis (without image - should error)
curl -X POST http://localhost:8080/analyze-image \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What do you see in this image?"
  }'

# 11. Image Analysis with Base64 Image
curl -X POST http://localhost:8080/analyze-image \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Describe what you see in this image",
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
    "image_format": "png"
  }'

# 12. Test with Empty Payload
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{}'

# 13. Test with Large Prompt
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "pro",
    "prompt": "Write a detailed analysis of the following topics: artificial intelligence, machine learning, deep learning, neural networks, natural language processing, computer vision, robotics, and their interconnections. Please provide examples and real-world applications for each."
  }'

# 14. Performance Test - Multiple Quick Requests
for i in {1..5}; do
  curl -X POST http://localhost:8080/chat/micro \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"Quick test $i\"}" &
done
wait

# 15. Test Malformed JSON (Error Handling)
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", invalid_json}'

# 16. Test with Different Content Types
curl -X POST http://localhost:8080 \
  -H "Content-Type: text/plain" \
  -d "This is plain text"

# 17. Test Image Generation with Titan - Complex Scene
curl -X POST http://localhost:8080/generate-image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A detailed architectural drawing of a modern sustainable building with solar panels, green walls, and innovative design elements",
    "image_params": {
      "width": 1024,
      "height": 1024,
      "cfg_scale": 9.0
    }
  }'

# 18. Stress Test - Large Batch
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sonic",
    "prompt": "Generate 10 creative writing prompts for science fiction stories"
  }'

# 19. Test Model Fallback (using non-existent model)
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nonexistent",
    "prompt": "This should fallback to pro model"
  }'

# 20. Integration Test - Canvas Model
curl -X POST http://localhost:8080/chat/canvas \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a description of a visual scene for image generation"
  }'
