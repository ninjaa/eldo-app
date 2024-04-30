import psutil
from datetime import datetime
from constants import UPLOAD_DIRECTORY
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from utils.video.generate_scene_video import generate_scene_body_video
from lib.scene_operations.process_title_scene import process_title_scene
from models.video import Video
from bson.objectid import ObjectId
from lib.database import get_db_connection
from lib.logger import setup_logger

from models.asset import Asset
from models.scene import Scene

_client, db = get_db_connection()

logger = setup_logger(__name__)


def load_asset(asset_filename):
    """
    Load an asset from the database given its filename.

    :param asset_filename: The filename of the asset to load.
    :return: An instance of the Asset class if found, None otherwise.
    """
    asset_result = db.assets.find_one({"filename": asset_filename})
    if asset_result:
        # Assuming Asset is a class that can be initialized with the database record
        return Asset(**asset_result)
    else:
        return None


def preprocess_and_expand_scenes(video_id):
    logger.info(f"Preprocessing and expanding scenes for video {video_id}")
    scene_results = list(db.scenes.find({'video_id': video_id}).sort('_id', 1))
    for scene_result in scene_results:
        scene = Scene(**scene_result)
        if scene.scene_type == "body" and scene.asset_filenames:
            for asset_filename in scene.asset_filenames:
                asset = load_asset(asset_filename)
                if asset and asset.metadata.content_type.startswith("video") and len(asset.transcript) > 0:
                    logger.info(
                        f"Preprocessing and expanding scene {scene_result['_id']} with asset {asset_filename}")
                    # Create a new scene for the "has_speech" part
                    has_speech_scene = scene_result.copy()
                    has_speech_scene.update({
                        '_id': str(ObjectId()),
                        'scene_type': 'has_speech',
                        'status': 'narration_complete',
                        'narration': asset.transcript,
                        'duration': asset.metadata.duration,
                        # Include only the relevant asset
                        'asset_filenames': [asset_filename],
                        'prev_scene_id': scene_result['_id'],
                        'next_scene_id': scene_result.get('next_scene_id', None)
                    })
                    logger.info(
                        f"Inserting new scene {has_speech_scene['_id']}")

                    # Insert the new "has_speech" scene into the database
                    db.scenes.insert_one(has_speech_scene)

                    # Update the 'next_scene_id' of the original scene to point to the new "has_speech" scene
                    db.scenes.update_one({'_id': scene_result['_id']}, {
                                         '$set': {
                                             'scene_type': 'title',
                                             'asset_filenames': [],
                                             'next_scene_id': has_speech_scene['_id']
                                         }})

    return True


def fetch_ready_video():
    # Fetches first videos that is ready for production
    videos = db.videos.find({'status': 'scene_extraction_complete'})

    for video in videos:
        # Check if all scenes of this video are in 'narration_complete' state
        scenes = list(db.scenes.find({'video_id': video['_id']}))
        if all(scene['status'] == 'narration_complete' for scene in scenes):
            return video['_id']


def concatenate_videos(video: Video, scene_video_paths):
    # Load video clips
    video_clips = [VideoFileClip(path) for path in scene_video_paths]

    # Apply fade-in and fade-out effects
    for i, clip in enumerate(video_clips):
        if i != 0:  # Skip fade-in for the first clip
            clip = clip.fadein(0.5)
        if i != len(video_clips) - 1:  # Skip fade-out for the last clip
            clip = clip.fadeout(0.5)
        video_clips[i] = clip

    # Concatenate video clips
    final_clip = concatenate_videoclips(video_clips)

    output_directory = os.path.join(
        UPLOAD_DIRECTORY, video.request_id, video.aspect_ratio, "final_cut")
    os.makedirs(output_directory, exist_ok=True)
    # Generate output path for the final cut
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    final_cut_path = os.path.join(
        output_directory, f"final_cut_{timestamp}.mp4")

    # Write the final cut to the output path
    final_clip.write_videofile(final_cut_path)

    # Close the video clips
    for clip in video_clips:
        clip.close()

    return final_cut_path


def monitor_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_usage_mb = memory_info.rss / 1024 / 1024
    print(f"Memory usage: {memory_usage_mb:.2f} MB")


async def process_video(video_id, generate_img2video=False, force_regenerate=False, update_db=False):
    # Load the video
    video_result = db.videos.find_one({'_id': video_id})
    if not video_result:
        logger.error(f"Video {video_id} not found.")
        return

    video = Video(**video_result)

    # Load and order the scenes
    scene_results = list(db.scenes.find({'video_id': video_id}))
    ordered_scene_results = order_scene_results(scene_results)

    # Process each scene and generate scene videos
    scene_video_paths = []
    for scene_result in ordered_scene_results:
        scene = Scene(**scene_result)
        monitor_memory_usage()
        scene_video_path = await generate_scene_video(video, scene, generate_img2video=generate_img2video, force_regenerate=force_regenerate)
        if scene_video_path:
            logger.info(f"Generated scene video path: {scene_video_path}")
            scene_video_paths.append(scene_video_path)

    # Concatenate scene videos into the final cut
    final_cut_path = concatenate_videos(video, scene_video_paths)

    logger.info(f"Final cut path: {final_cut_path}")

    if update_db:
        # Update video status
        db.videos.update_one({'_id': video_id}, {
            '$set': {
                'status': 'processing_complete',
                'final_cut_path': final_cut_path
            }})


def order_scene_results(scene_results):
    # Order scenes based on the linked list structure
    ordered_scenes = []
    scene_map = {scene['_id']: scene for scene in scene_results}
    current_scene_id = next(
        (scene['_id'] for scene in scene_results if not scene.get('prev_scene_id')), None)

    while current_scene_id:
        current_scene = scene_map[current_scene_id]
        ordered_scenes.append(current_scene)
        current_scene_id = current_scene.get('next_scene_id')

    return ordered_scenes


async def fetch_and_process_videos(generate_img2video=False, force_regenerate=False):
    video_id = fetch_ready_video()
    if video_id:
        logger.info(f"Processing video {video_id}")
        preprocess_and_expand_scenes(video_id)
        await process_video(video_id, generate_img2video=generate_img2video, force_regenerate=force_regenerate)
    else:
        logger.info("No videos ready for processing.")


async def generate_scene_video(video: Video, scene: Scene, force_regenerate=False, generate_img2video=False):
    logger.info(
        f"Generating scene video for scene {scene.scene_type} {scene.id}")

    if not force_regenerate and scene.generated_scene_video:
        logger.info(
            f"Using existing generated scene video: {scene.generated_scene_video}")
        return scene.generated_scene_video

    if scene.scene_type == "body":
        scene_video_path = await generate_scene_body_video(video, scene, add_subtitles=True, add_narration=True, generate_img2video=generate_img2video)
    elif scene.scene_type == "has_speech":
        scene_video_path = await generate_scene_body_video(video, scene, add_subtitles=True, add_narration=False, generate_img2video=generate_img2video)
    elif scene.scene_type in ["title", "middle_title", "outro"]:
        if scene.scene_type == "title":
            gradient_color = (173, 216, 230)
            gradient_color2 = (0, 0, 139)
        elif scene.scene_type == "middle_title":
            gradient_color = (255, 192, 203)  # Light pink
            gradient_color2 = (255, 105, 180)  # Hot pink
        elif scene.scene_type == "outro":
            gradient_color = (0, 0, 139)
            gradient_color2 = (173, 216, 230)

        scene_video_path = await process_title_scene(scene, gradient_color=gradient_color, gradient_color2=gradient_color2)

    if scene_video_path:
        # Update the scene with the generated video path
        db.scenes.update_one({'_id': scene.id}, {
                             '$set': {'generated_scene_video': scene_video_path}})

    return scene_video_path
