#!/bin/bash

# Send the JSON request to retrieve the video ID
response=$(curl -X POST -H "Content-Type: application/json" -d @video_request.json http://127.0.0.1:8000/video-request/)

# Extract the video ID from the response
request_id=$(echo "$response" | jq -r '.request_id')

# Print the video ID
echo "Video ID: $request_id"

# Loop through all files in the current directory
for file in *; do
    # Check if the file has a .mp4 or .jpg extension
    if [[ $file == *.mp4 || $file == *.jpg ]]; then
        # Make the curl request with the file and video ID
        curl -X POST -H "Content-Type: multipart/form-data" -F "file=@$file" "http://127.0.0.1:8000/video-request/$request_id/media"
    fi
done

curl -X POST -H "Content-Type: application/json" http://127.0.0.1:8000/video-request/$request_id/finalize