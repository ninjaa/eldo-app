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
        if scene.scene_type == "body" and scene.asset_filename:
            asset = load_asset(scene.asset_filename)
            if asset and asset.metadata.content_type.startswith("video") and len(asset.transcript) > 0:
                logger.info(
                    f"Preprocessing and expanding scene {scene_result['_id']}")
                # Update the original scene's status and clear the asset_filename
                # Create a new scene for the "has_speech" part
                has_speech_scene = scene_result.copy()
                has_speech_scene.update({
                    '_id': str(ObjectId()),
                    'scene_type': 'has_speech',
                    'status': 'narration_complete',
                    'narration': asset.transcript,
                    'duration': asset.metadata.duration,
                    'prev_scene_id': scene_result['_id'],
                    'next_scene_id': scene_result.get('next_scene_id', None)
                })
                logger.info(f"Inserting new scene {has_speech_scene['_id']}")

                # Insert the new "has_speech" scene into the database
                db.scenes.insert_one(has_speech_scene)

                # Update the 'next_scene_id' of the original scene to point to the new "has_speech" scene
                db.scenes.update_one({'_id': scene_result['_id']}, {
                                     '$set': {
                                         'scene_type': 'title',
                                         'asset_filename': '',
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


def process_video(video_id):
    pass

    # # Process each scene based on its type and requirements
    # for scene in scenes:
    #     if scene['scene_type'] == 'title':
    #         # Apply specific operations for title scenes
    #         pass
    #     elif scene['scene_type'] == 'body':
    #         # Apply operations for body scenes
    #         pass
    #     # Add more conditions as necessary based on scene specifics


def fetch_and_process_videos():
    video_id = fetch_ready_video()
    if video_id:
        logger.info(f"Processing video {video_id}")
        preprocess_and_expand_scenes(video_id)
        process_video(video_id)
    else:
        logger.info("No videos ready for processing.")
