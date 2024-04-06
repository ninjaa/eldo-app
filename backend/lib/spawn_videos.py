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
from utils.exception_helpers import log_exception

logger = setup_logger(__name__)

NO_VIDEO_REQUEST_FORMATS_WAIT_SECONDS = 5
MAX_SPAWNING_ATTEMPTS = 3

_client, db = get_db_connection()
video_requests_collection = db.video_requests
videos_collection = db.videos
uploads_collection = db.uploads
video_request_aspect_ratios_collection = db.video_request_aspect_ratios
video_request_formats_collection = db.video_request_formats


async def spawn_video_from_video_request_format(format_id: str, change_status=True, insert_videos=True):
    try:
        video_request_format_result = video_request_formats_collection.find_one({
                                                                         "_id": format_id})
        video_request_format = VideoRequestFormat(**video_request_format_result)

        video_requests_result = video_requests_collection.find_one(
            {"_id": video_request_format.request_id})
        video_request = VideoRequest(**video_requests_result)

        if video_request:
            video_id = str(ObjectId())
            video_dict = {
                "_id": video_id,
                "request_id": video_request.id,
                "lang": video_request.lang,
                "topic": video_request.topic,
                "style": video_request.style,
                "status": "requested",
                "aspect_ratio": video_request_format.aspect_ratio,
                "length": video_request_format.length
            }
            video = Video(**video_dict)

            inserted = False
            if insert_videos:
                inserted = True
                videos_collection.insert_one(video.model_dump(by_alias=True))

            if change_status:

                spawning_end_time = datetime.datetime.now()
                spawning_duration = (
                    spawning_end_time - video_request_format.spawning_start_time).total_seconds()
                video_request_formats_collection.update_one(
                    {"_id": format_id},
                    {"$set": {
                        "status": "spawning_complete",
                        "spawning_end_time": spawning_end_time,
                        "spawning_duration": spawning_duration
                    }}
                )

            return AppResponse(
                status="success",
                data={
                    "video_id": video_id,
                    "format_id": format_id,
                    "request_id": video_request_format.request_id,
                    "message": "Video validated, " + ("inserted" if inserted else "not inserted"),
                    "video": video,
                    "inserted": inserted
                }
            )
        else:
            return AppResponse(
                status="error",
                error={
                    "video_id": video_id,
                    "format_id": format_id,
                    "message": "Video Request not found"
                }
            )
    except Exception as e:
        video_request_format = video_request_formats_collection.find_one({
                                                                         "_id": format_id})
        video_request_format = VideoRequestFormat(**video_request_format)

        if video_request_format.spawning_attempts + 1 >= MAX_SPAWNING_ATTEMPTS and change_status:
            video_request_format.update_one(
                {"_id": format_id},
                {"$set": {"status": "spawning_failed"}}
            )
            return AppResponse(
                status="error",
                error={
                    "format_id": format_id,
                    "message": f"Video Request Format spawning Videos failed after {MAX_SPAWNING_ATTEMPTS} attempts"
                }
            )
        else:
            if change_status:
                video_request_formats_collection.update_one(
                    {"_id": format_id},
                    {"$inc": {"spawning_attempts": 1},
                        "$set": {"status": "requested"}}
                )
            return AppResponse(
                status="error",
                error={
                    "format_id": format_id,
                    "message": f"An exception occurred: {e}"
                }
            )


def fetch_next_video_request_format_for_video_spawning(change_status=True):
    aspect_ratios_converted = video_request_aspect_ratios_collection.distinct(
        "aspect_ratio",
        {
            "status": "converted"
        }
    )

    video_request_format = video_request_formats_collection.find_one(
        {
            "status": "requested",
            "aspect_ratio": {
                "$in": aspect_ratios_converted
            }
        },
        sort=[("_id", pymongo.ASCENDING)]
    )

    if video_request_format:
        if change_status:
            video_request_formats_collection.update_one(
                {"_id": video_request_format["_id"]},
                {
                    "$set": {
                        "spawning_start_time": datetime.datetime.now(),
                        "spawning_end_time": None,
                        "status": "spawning_started"
                    }
                }
            )
        return AppResponse(
            status="success",
            data={"format_id": video_request_format["_id"]}
        )
    else:
        return AppResponse(
            status="success",
            data={"format_id": None,
                  "message": "No ready video request format found"}
        )


async def find_video_request_formats_and_spawn_videos(max_count=None, batch_size=1, change_status=True, insert_videos=True):
    processed_count = 0
    while True:
        try:
            batch = []
            remaining_count = max_count - processed_count if max_count is not None else batch_size
            for _ in range(min(batch_size, remaining_count)):
                fetch_next_video_request_format_result = fetch_next_video_request_format_for_video_spawning(
                    change_status=change_status)
                format_id = fetch_next_video_request_format_result.data.get(
                    'format_id', None)
                if format_id:
                    batch.append(format_id)
                else:
                    break

            if not batch:
                # Wait for a short time if no video_requests are found
                logger.info(
                    f"No video request formats found. Sleeping for {NO_VIDEO_REQUEST_FORMATS_WAIT_SECONDS} seconds.")
                await asyncio.sleep(NO_VIDEO_REQUEST_FORMATS_WAIT_SECONDS)
                continue

            results = await asyncio.gather(*[spawn_video_from_video_request_format(
                format_id,
                change_status=change_status,
                insert_videos=insert_videos
            ) for format_id in batch])

            for result in results:
                if result.status == "error":
                    logger.info(
                        f"Failed to spawn videos for request format {result.error['format_id']}: {result.error['message']}")
                elif result.status == "success":
                    logger.info(
                        f"Successfully spawned videos for request {result.data['format_id']}", extra={"data": result.data})

            processed_count += len(batch)
            if max_count is not None and processed_count >= max_count:
                break

        except Exception as e:
            log_exception(logger, e)
