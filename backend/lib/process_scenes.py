from lib.database import get_db_connection
from lib.logger import setup_logger

_client, db = get_db_connection()

logger = setup_logger(__name__)


def fetch_video_and_ready_scenes():
    # Fetch videos that are ready for processing
    videos = db.videos.find({'status': 'script_generated'})

    ready_scenes = []
    for video in videos:
        # Check if all scenes of this video are in 'narration_complete' state
        scenes = list(db.scenes.find({'video_id': video['_id']}))
        if all(scene['status'] == 'narration_complete' for scene in scenes):
            ready_scenes.extend(scenes)
            return video, ready_scenes


def process_video(scenes):
    # Process each scene based on its type and requirements
    for scene in scenes:
        if scene['scene_type'] == 'title':
            # Apply specific operations for title scenes
            pass
        elif scene['scene_type'] == 'body':
            # Apply operations for body scenes
            pass
        # Add more conditions as necessary based on scene specifics


def fetch_and_process_videos():
    result = fetch_video_and_ready_scenes()
    if result:
        _video, scenes = result
        process_video(scenes)
    else:
        logger.info("No videos ready for processing.")
