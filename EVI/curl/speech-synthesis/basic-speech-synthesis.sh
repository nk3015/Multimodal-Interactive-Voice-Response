#!/bin/bash

# Set your API Key
HUME_API_KEY="7fuEmAF8DkxdGUG0gNkVAIWtIbL2wG3SQHX9wiPFSM2zb2my"

# Send the POST request and save the response
curl -X POST "https://api.hume.ai/v0/tts" \
     -H "Content-Type: application/json" \
     -H "X-Hume-Api-Key: $HUME_API_KEY" \
     -d '{
       "utterances": [
         {
           "text": "Welcome to my application!",
           "description": "A friendly and professional voice"
         }
       ]
     }' -o response.json

# Extract and decode the audio data
jq -r '.generations[0].audio' response.json | base64 --decode > output_audio.mp3

# Play the audio
mpg123 output_audio.mp3

#src: https://dev.hume.ai/docs/text-to-speech-tts/overview