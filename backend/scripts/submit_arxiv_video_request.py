import requests
import os
import json
import glob


def submit_video_request(folder_path):
    # Read the topic from script.txt
    with open(os.path.join(folder_path, 'script.txt'), 'r') as file:
        topic = file.read().strip()

    # Prepare the video request data
    video_request_data = {
        "lang": "english",
        "topic": topic,
        "style": "technical announcement",
        "status": "pending",
        "brand_link": "https://twitter.com/aditya_advani",
        "formats": [{"aspect_ratio": "9x16", "length": 180}]
    }

    # Send the video request
    response = requests.post(
        "http://127.0.0.1:8000/video-request/", json=video_request_data)
    response_data = response.json()
    request_id = response_data.get('request_id')

    print(f"Video ID: {request_id}")

    # Function to upload files
    def upload_file(file_path):
        with open(file_path, 'rb') as file:
            files = {'file': file}
            requests.post(
                f"http://127.0.0.1:8000/video-request/{request_id}/media", files=files)

    # Upload images from images/ folder
    images_folder = os.path.join(folder_path, 'images')
    for file in os.listdir(images_folder):
        if 'cropped' in file:
            upload_file(os.path.join(images_folder, file))

    # Upload files from uploads/ folder
    uploads_folder = os.path.join(folder_path, 'uploads')
    for file in os.listdir(uploads_folder):
        upload_file(os.path.join(uploads_folder, file))

    # Upload files from diagrams/ folder
    diagrams_folder = os.path.join(folder_path, 'diagrams')
    for file in os.listdir(diagrams_folder):
        upload_file(os.path.join(diagrams_folder, file))

        # Parse the JSON file for figure list
    json_files = glob.glob(os.path.join(folder_path, '*_figure_list.json'))
    if json_files:
        with open(json_files[0], 'r') as json_file:
            figure_list = json.load(json_file)

        # Upload and post annotations for matched diagrams
        diagrams_folder = os.path.join(folder_path, 'diagrams')
        for figure in figure_list:
            # import pdb; pdb.set_trace()
            image_name = figure['image_name']
            image_caption = figure['image_caption']
            image_description = figure['image_descriptions']

            # Use glob to find matching files
            diagram_path_pattern = os.path.join(
                diagrams_folder, f"{image_name}.*")
            matching_files = glob.glob(diagram_path_pattern)
            if matching_files:
                diagram_path = matching_files[0]  # Take the first match
                asset_filename = os.path.basename(
                    diagram_path)  # Extract filename from path
                # Post the caption, description, and filename as JSON
                annotation_data = {
                    "asset_filename": asset_filename,
                    "image_caption": image_caption,
                    "image_description": image_description
                }
                requests.post(
                    f"http://127.0.0.1:8000/video-request/{request_id}/annotations",
                    json=annotation_data
                )

    # Finalize the video request
    requests.post(f"http://127.0.0.1:8000/video-request/{request_id}/finalize")


if __name__ == "__main__":
    folder_path = input("Enter the folder path: ")
    submit_video_request(folder_path)
