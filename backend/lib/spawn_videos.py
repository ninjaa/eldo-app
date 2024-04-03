import asyncio
import datetime
import pymongo
from lib.database import get_db_connection
from lib.logger import setup_logger
from lib.models import AppResponse, VideoRequest, Video

logger = setup_logger(__name__)

NO_VIDEO_REQUESTS_WAIT_SECONDS = 5
MAX_SPAWNING_ATTEMPTS = 3

_client, _db,  video_requests_collection, videos_collection, assets = get_db_connection()


async def spawn_videos_from_video_requests(request_id: str, change_status=True, insert_videos=True):
    # import pdb
    # pdb.set_trace()
    try:
        # Find the Video Request by its ID
        video_requests_result = video_requests_collection.find_one(
            {"_id": request_id})

        video_request = VideoRequest(**video_requests_result)
        if video_request:
            # Create video objects for each requested format
            videos = []
            for format in video_request.formats:
                video_dict = {
                    "request_id": request_id,
                    "lang": video_request.lang,
                    "topic": video_request.topic,
                    "style": video_request.style,
                    "status": "spawned",
                    "aspect_ratio": format.aspect_ratio,
                    "length": format.length
                }
                video = Video(**video_dict)

                if insert_videos:
                    video_insertion_result = videos_collection.insert_one(
                        video.model_dump(by_alias=True))
                    video.id = video_insertion_result.inserted_id

                videos.append(video)
            return AppResponse(
                status="success",
                data={
                    "request_id": request_id,
                    "message": "Videos created",
                    "videos": videos
                }
            )
        else:
            return AppResponse(
                status="error",
                error={
                    "request_id": request_id,
                    "message": "Video Request not found"
                }
            )
    except Exception as e:
        video_request_result = video_requests_collection.find_one(
            {"_id": request_id})
        video_request = VideoRequest(**video_request_result)

        if video_request.spawning_attempts + 1 >= MAX_SPAWNING_ATTEMPTS and change_status:
            video_requests_collection.update_one(
                {"_id": request_id},
                {"$set": {"status": "spawning_failed"}}
            )
            return AppResponse(
                status="error",
                error={
                    "request_id": request_id,
                    "message": f"Video Request spawning Videos failed after {MAX_SPAWNING_ATTEMPTS} attempts"
                }
            )

        else:
            if change_status:
                video_requests_collection.update_one(
                    {"_id": request_id},
                    {"$inc": {"spawning_attempts": 1},
                     "$set": {"status": "requested"}}
                )
            return AppResponse(
                status="error",
                error={
                    "request_id": request_id,
                    "message": f"An exception occurred: {e}"
                }
            )


def fetch_next_video_request_for_video_spawning(change_status=True):
    excluded_request_ids = assets.distinct(
        "request_id",
        {
            "status": {"$nin": ["description_complete"]}
        }
    )

    video_request = video_requests_collection.find_one(
        {
            "status": "requested",
            "_id": {
                "$nin": excluded_request_ids
            }
        },
        sort=[("_id", pymongo.ASCENDING)]
    )

    if video_request:
        if change_status:
            video_requests_collection.update_one(
                {"_id": video_request["_id"]},
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
            data={"request_id": video_request["_id"]}
        )
    else:
        return AppResponse(
            status="success",
            data={"request_id": None,
                  "message": "No video request found"}
        )


async def find_video_requests_and_spawn_videos(max_count=None, batch_size=1, change_status=True, insert_videos=True):
    processed_count = 0
    while True:
        try:
            batch = []
            remaining_count = max_count - processed_count if max_count is not None else batch_size
            for _ in range(min(batch_size, remaining_count)):
                video_request_result = fetch_next_video_request_for_video_spawning(
                    change_status=change_status)
                request_id = video_request_result.data.get('request_id', None)
                if request_id:
                    batch.append(request_id)
                else:
                    break

            if not batch:
                # Wait for a short time if no video_requests are found
                logger.info(
                    f"No video requests found. Sleeping for {NO_VIDEO_REQUESTS_WAIT_SECONDS} seconds.")
                await asyncio.sleep(NO_VIDEO_REQUESTS_WAIT_SECONDS)
                continue

            results = await asyncio.gather(*[spawn_videos_from_video_requests(
                request_id,
                change_status=change_status,
                insert_videos=insert_videos
            ) for request_id in batch])

            for result in results:
                if result.status == "error":
                    logger.info(
                        f"Failed to spawn videos for request {result.error['request_id']}: {result.error['message']}")
                elif result.status == "success":
                    logger.info(
                        f"Successfully spawned videos for request {result.data['request_id']}", extra={ "data": result.data })

            processed_count += len(batch)
            if max_count is not None and processed_count >= max_count:
                break

        except Exception as e:
            print(f"An exception occurred: {e}")
