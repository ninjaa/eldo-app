from bson.objectid import ObjectId
import asyncio
import datetime
import pymongo
from lib.database import get_db_connection
from lib.logger import setup_logger
from models.app_response import AppResponse
from models.video_request import VideoRequest
from models.video_request_format import VideoRequestFormat
from models.video import Video

logger = setup_logger(__name__)

NO_VIDEO_SCRIPTS_WAIT_SECONDS = 5
MAX_GENERATION_ATTEMPTS = 3

_client, db = get_db_connection()
video_requests_collection = db.video_requests
videos_collection = db.videos
uploads_collection = db.uploads
assets_collection = db.assets
video_request_aspect_ratios_collection = db.video_request_aspect_ratios
video_request_formats_collection = db.video_request_formats


async def generate_script(video_id, change_status=True):
    video = Video(**videos_collection.find_one({"_id": video_id}))
    assets = list(assets_collection.find(
        {
            "status": "converted",
            "request_id": video.request_id,
            "metadata.aspect_ratio": video.aspect_ratio
        }))
    print(assets)
    print(video)


def fetch_next_video_for_script_generation(change_status=True):
    video_result = videos_collection.find_one(
        {
            "status": "requested",
        },
        sort=[("_id", pymongo.ASCENDING)]
    )

    if video_result:
        video = Video(**video_result)
        if change_status:
            videos_collection.update_one(
                {"_id": video.id},
                {
                    "$set": {
                        "script_generation_processing_start_time": datetime.datetime.now(),
                        "script_generation_processing_end_time": None,
                        "status": "spawning_started"
                    }
                }
            )
        return AppResponse(
            status="success",
            data={"video_id": video.id}
        )
    else:
        return AppResponse(
            status="success",
            data={"video_id": None,
                  "message": "No ready video found for script generation"}
        )


async def find_videos_and_generate_scripts(max_count=None, batch_size=1, change_status=True):
    processed_count = 0
    while True:
        try:
            batch = []
            remaining_count = max_count - processed_count if max_count else None
            for _ in range(batch_size):
                video_result = fetch_next_video_for_script_generation(
                    change_status=change_status)
                if video_result.status == "success" and video_result.data["video_id"]:
                    batch.append(video_result.data["video_id"])
                    processed_count += 1
                    if remaining_count and processed_count >= remaining_count:
                        break
            if not batch:
                # Wait for a short time if no video_requests are found
                logger.info(
                    f"No videos for script generation found. Sleeping for {NO_VIDEO_SCRIPTS_WAIT_SECONDS} seconds.")
                await asyncio.sleep(NO_VIDEO_SCRIPTS_WAIT_SECONDS)
                continue

            results = await asyncio.gather(*[generate_script(video_id, change_status=change_status) for video_id in batch])
            processed_count += len(batch)
            if max_count is not None and processed_count >= max_count:
                break
        except Exception as e:
            logger.error(f"Error processing videos: {e}")
            break
