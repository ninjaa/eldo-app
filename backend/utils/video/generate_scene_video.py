import os
from constants import UPLOAD_DIRECTORY
from models.video import Video
from moviepy.editor import ImageClip, concatenate_videoclips, VideoFileClip
from models.asset import Asset
from models.scene import Scene
from lib.database import get_db_connection
from utils.image.image_helpers import get_image_prompts
from utils.image.generate_sd_image import generate_image
import datetime

_client, db = get_db_connection()


def asset_is_video(asset: Asset) -> bool:
    return asset.metadata.content_type.startswith("video")


def asset_is_image(asset: Asset) -> bool:
    return asset.metadata.content_type.startswith("image")


def get_video_clip(filename: str, duration: float = None):
    """
    Retrieves a video clip object from a filename. Optionally trims the clip to a specified duration.

    :param filename: The path to the video file.
    :param duration: The duration to which the video should be trimmed (in seconds).
    :return: A VideoFileClip object.
    """
    clip = VideoFileClip(filename)
    if duration is not None and duration < clip.duration:
        # Trim the clip to the specified duration
        clip = clip.subclip(0, duration)
    return clip


async def generate_scene_video_no_speech(video: Video, scene: Scene, add_subtitles=False):
    # import pdb
    # pdb.set_trace()
    total_asset_duration = 0
    clips = []

    # 1. Check if the scene has an asset_filename
    if scene.asset_filename:
        asset_result = db.assets.find_one({"filename": scene.asset_filename})
        asset = None
        if asset_result:
            asset = Asset(**asset_result)

        if asset:
            # Assuming you have a way to determine if an asset is a video or image
            if asset_is_video(asset):
                # 2. Use the video's duration
                asset_duration = min(asset.metadata.duration, scene.duration)
                clips.append(get_video_clip(
                    scene.asset_filename, asset_duration))
                total_asset_duration += asset_duration
            elif asset_is_image(scene.asset_filename):
                # 3. For an image, use a fixed duration of 2.5 seconds
                clips.append(ImageClip(scene.asset_filename).set_duration(2.5))
                total_asset_duration += 2.5

    # 4. Calculate the gap and generate additional images if needed
    gap_duration = scene.duration - total_asset_duration

    # Calculate the number of images to generate
    num_images = int(gap_duration // 2.5) + \
        (1 if gap_duration % 2.5 > 0 else 0)

    # Generate prompts and durations
    image_prompts = get_image_prompts(num_images, scene, video)
    image_prompts_and_durations = []
    for prompt in image_prompts:
        duration = 2.5 if gap_duration >= 2.5 else gap_duration
        # Append to the new list instead
        image_prompts_and_durations.append((prompt, duration))
        gap_duration -= duration

    for index, (image_prompt, clip_duration) in enumerate(image_prompts_and_durations):
        # Use the minimum of gap_duration and 2.5 seconds for the last clip
        generated_image_path = generate_image(scene, image_prompt, index)
        clips.append(
            ImageClip(generated_image_path).set_duration(clip_duration))

    # 5. Convert images to video clips and concatenate
    final_clip = concatenate_videoclips(clips)
    final_clip.set_duration(scene.duration)

    # Save the final video
    output_dir = f"{UPLOAD_DIRECTORY}/{scene.request_id}/{scene.aspect_ratio}/scene_videos"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        output_dir, f"{scene.id}_final_scene_{timestamp}.mp4")
    final_clip.write_videofile(output_path, fps=24)

    return output_path
