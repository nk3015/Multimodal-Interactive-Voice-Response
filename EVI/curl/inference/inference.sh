# Set your API Key
HUME_API_KEY="7fuEmAF8DkxdGUG0gNkVAIWtIbL2wG3SQHX9wiPFSM2zb2my"


curl -X POST https://api.hume.ai/v0/batch/jobs \
     -H "X-Hume-Api-Key: $HUME_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
  "urls": [
    "https://hume-tutorials.s3.amazonaws.com/faces.zip"
  ],
  "notify": true
}'