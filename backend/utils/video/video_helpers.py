import cv2
import openai
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
import tempfile
import os
from utils.image.image_helpers import describe_image

load_dotenv()



def get_video_size(video_path):
    # Open the video file
    video = cv2.VideoCapture(video_path)

    # Get the video's width and height
    width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)

    # Close the video file
    video.release()

    # Return the width and height
    return int(width), int(height)


def extract_and_describe_frames(video_path, interval=4):
    # Load the video clip
    video = VideoFileClip(video_path)

    # Calculate the duration of the video in seconds
    duration = video.duration

    # Initialize a list to store the descriptions
    descriptions = []

    # Create a temporary directory to store the extracted frames
    with tempfile.TemporaryDirectory() as temp_dir:
        # Iterate over the frames at the desired interval
        for t in range(0, int(duration), interval):
            # Extract the frame at the current time
            frame = video.get_frame(t)

            # Save the frame as a temporary image file
            frame_path = os.path.join(temp_dir, f"frame_{t}.jpg")
            video.save_frame(frame_path, t=t)

            # Describe the frame using the describe_image function
            description = describe_image(frame_path)
            descriptions.append(description)

    # Combine the descriptions into a single string
    combined_description = ".\n".join(descriptions) + "."

    return combined_description


def summarize_description(long_description: str, transcript: str, duration: float) -> str:
    api_token = os.getenv("MISTRAL_API_KEY")
    client = openai.OpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key=api_token
    )

    prompt = f"""
    Please summarize this long description of a {duration} secs video into something succint. 
    If there is no transcript, then summarize the video description. Do not mention in the summary if there is no transcript or not.
    
    long_description: {long_description}
    transcript: {transcript}

    short_description:
    """

    print(prompt)

    chat_completion = client.chat.completions.create(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": "You are a video editor screenwriting and then cutting a TV news / social media video."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=1000
    )

    answer = chat_completion.choices[0].message.content.strip()
    print(f"summary description: {answer}")
    return answer


def detect_and_remove_black_bars(video):
    # Detect black bars on the sides
    left_bar = 0
    right_bar = video.w
    top_bar = 0
    bottom_bar = video.h

    for frame in video.iter_frames(dtype='uint8'):
        if frame[:, 0, :].mean() > 10:  # Check if the left bar is not black
            break
        left_bar += 1

    for frame in video.iter_frames(dtype='uint8'):
        if frame[:, -1, :].mean() > 10:  # Check if the right bar is not black
            break
        right_bar -= 1

    # Crop the video to remove the black bars
    cropped_video = video.crop(
        x1=left_bar, y1=top_bar, x2=right_bar, y2=bottom_bar)
    return cropped_video


# default codec is 'libx264'
# default bitrate is 2000
def convert_video_to_aspect_ratio(input_path, output_path, aspect_ratio_width, aspect_ratio_height, crop_type="contain", background_color=(0, 0, 0)):

    # Get the video size using the get_video_size function
    video_size = get_video_size(input_path)
    video_width = video_size['width']
    video_height = video_size['height']

    # Load the video clip
    video = VideoFileClip(input_path)

    # Calculate the current aspect ratio
    current_aspect_ratio = video_width / video_height
    print(f"video width is {video_width}")
    print(f"video height is {video_height}")
    print(f"current aspect ratio is {current_aspect_ratio}")
    print(
        f"desired aspect ratio is {aspect_ratio_width} / {aspect_ratio_height}")
    # Check if the video is already in the desired aspect ratio
    if current_aspect_ratio == aspect_ratio_width / aspect_ratio_height:
        print("The video is already in the desired aspect ratio.")
        return

    # Calculate the new dimensions based on the desired aspect ratio
    desired_aspect_ratio = aspect_ratio_width / aspect_ratio_height
    if crop_type == "contain":
        if current_aspect_ratio > desired_aspect_ratio:
            new_height = int(video_width / desired_aspect_ratio)
            new_width = video_width
        else:
            new_width = int(video_height * desired_aspect_ratio)
            new_height = video_height

        # Create a new background clip with the desired dimensions and color
        background_clip = ColorClip(
            size=(new_width, new_height), color=background_color)

        # Calculate the position to center the video on the background
        x_position = (new_width - video_width) // 2
        y_position = (new_height - video_height) // 2

        # Overlay the video on the background
        final_clip = CompositeVideoClip(
            [background_clip, video.set_position((x_position, y_position))])
        final_clip = final_clip.set_duration(video.duration)
    else:
        if current_aspect_ratio > desired_aspect_ratio:
            new_width = int(video_height * desired_aspect_ratio)
            new_height = video_height
        else:
            new_width = video_width
            new_height = int(video_width / desired_aspect_ratio)

        # Crop the video to the new dimensions
        x1 = (video_width - new_width) // 2
        y1 = (video_height - new_height) // 2
        x2 = x1 + new_width
        y2 = y1 + new_height
        final_clip = video.crop(x1=x1, y1=y1, x2=x2, y2=y2)

    # Write the final clip to a file
    final_clip.write_videofile(
        output_path)
