from lib.logger import setup_logger
import asyncio
import cv2
import openai
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip
import tempfile
import os
from utils.image.image_helpers import describe_image

load_dotenv()

logger = setup_logger(__name__)


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


async def extract_and_describe_frames(video_path, interval=4):
    # Load the video clip
    video = VideoFileClip(video_path)

    # Calculate the duration of the video in seconds
    duration = video.duration

    # Initialize a list to store the description tasks
    description_tasks = []

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

# Create a task for describing the frame
            description_task = describe_image(frame_path)
            description_tasks.append(description_task)

            # If the number of tasks reaches 2 or it's the last frame, await the tasks
            if len(description_tasks) == 2 or t + interval >= duration:
                batch_descriptions = await asyncio.gather(*description_tasks)
                # Extend the descriptions list
                descriptions.extend(batch_descriptions)
                description_tasks = []  # Reset the task list

            # Describe the frame using the describe_image function
            description = await describe_image(frame_path)
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

