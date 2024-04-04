# for each next 'requested' format
# we will check that all media uploads are in description_complete status
# for each upload
# convert to format aspect ratio
# if all uploads have been converted to the aspect ratio within, we will update the status of the video_request_format to "converted"

from constants import UPLOAD_DIRECTORY
import asyncio
import datetime
import os
import pymongo
from moviepy.editor import VideoFileClip
from lib.database import get_db_connection
from lib.logger import setup_logger
from models.asset import Asset
from models.app_response import AppResponse
from models.upload import Upload
from models.video_request_aspect_ratio import VideoRequestAspectRatio
from utils.image.image_helpers import detect_image_size_and_aspect_ratio
from utils.image.resize_images import convert_image_to_aspect_ratio
from utils.video.resize_videos import convert_video_to_aspect_ratio
from utils.video.video_helpers import get_video_size
from bson.objectid import ObjectId

logger = setup_logger(__name__)
_client, db = get_db_connection()
assets_collection = db.assets
uploads_collection = db.uploads
video_request_aspect_ratios_collection = db.video_request_aspect_ratios


MAX_CONVERSION_ATTEMPTS = 3
NO_ASPECT_RATIOS_WAIT_SECONDS = 5


async def convert_uploads_to_aspect_ratio(aspect_ratio_id):
    try:

        aspect_ratio_result = video_request_aspect_ratios_collection.find_one(
            {"_id": aspect_ratio_id})

        if aspect_ratio_result:
            aspect_ratio = VideoRequestAspectRatio(**aspect_ratio_result)
            aspect_ratio_bits = aspect_ratio.aspect_ratio.split("x")
            aspect_ratio_width = int(aspect_ratio_bits[0])
            aspect_ratio_height = int(aspect_ratio_bits[1])
            request_id = aspect_ratio.request_id
            asset_directory_name = aspect_ratio.aspect_ratio
            asset_directory_path = os.path.join(
                UPLOAD_DIRECTORY, request_id, "assets", asset_directory_name)
            os.makedirs(asset_directory_path, exist_ok=True)
            uploads = uploads_collection.find(
                {"request_id": aspect_ratio.request_id})
            # @TODO parallelize asset conversion
            for upload_dict in uploads:
                conversion_start_time = datetime.datetime.now()
                upload = Upload(**upload_dict)
                asset_filename_without_extension = f"{upload.filename_without_extension}-{upload.metadata.content_type}-{aspect_ratio.aspect_ratio}"
                asset_filename = f"{asset_filename_without_extension}{upload.file_extension}"
                converted_asset_file_path = os.path.join(
                    asset_directory_path, asset_filename)

                if upload.metadata.content_type == "video":
                    convert_video_to_aspect_ratio(
                        upload.file_path,
                        converted_asset_file_path,
                        aspect_ratio_width,
                        aspect_ratio_height
                    )
                    clip = VideoFileClip(converted_asset_file_path)
                    video_width, video_height = get_video_size(
                        converted_asset_file_path)

                    metadata = {
                        "duration": clip.duration,
                        "width": video_width,
                        "height": video_height,
                        "aspect_ratio": aspect_ratio.aspect_ratio,
                        "fps": clip.fps,
                        "has_speech": upload.metadata.has_speech,
                        "content_type": "video"
                    }
                elif upload.metadata.content_type == "image":
                    convert_image_to_aspect_ratio(
                        upload.file_path, converted_asset_file_path, aspect_ratio_width, aspect_ratio_height)
                    image_width, image_height, _image_aspect_ratio = detect_image_size_and_aspect_ratio(
                        converted_asset_file_path)
                    metadata = {
                        "width": image_width,
                        "height": image_height,
                        "aspect_ratio": aspect_ratio.aspect_ratio,
                        "is_logo": upload.metadata.is_logo,
                        "is_profile_pic": upload.metadata.is_profile_pic,
                        "content_type": "image"
                    }

                asset_id = str(ObjectId())
                conversion_end_time = datetime.datetime.now()
                conversion_duration = (
                    conversion_end_time - conversion_start_time).total_seconds()
                asset_dict = {
                    "_id": asset_id,
                    "request_id": aspect_ratio.request_id,
                    "filename": asset_filename,
                    "file_extension": upload.file_extension,
                    "filename_without_extension": asset_filename_without_extension,
                    "file_path": converted_asset_file_path,
                    "content_type": upload.content_type,
                    "description": upload.description,
                    "transcript": upload.transcript,
                    "processed": upload.processed,
                    "status": "converted",
                    "metadata": metadata,
                    "conversion_start_time": conversion_start_time,
                    "conversion_end_time": conversion_end_time,
                    "conversion_duration": conversion_duration,
                }

                asset = Asset(**asset_dict)
                assets_collection.insert_one(asset.model_dump(by_alias=True))
        else:
            return AppResponse(
                status="error",
                error={
                    "aspect_ratio_id": aspect_ratio_id,
                    "message": f"Video Request Aspect Ratio with id {aspect_ratio_id} not found!"
                }
            )
        uploads = uploads_collection.find({"request_id": aspect_ratio_id})
    except Exception as e:
        if aspect_ratio_result:
            next_status = "requested"
            if aspect_ratio_result["conversion_attempts"] + 1 >= MAX_CONVERSION_ATTEMPTS:
                video_request_aspect_ratios_collection.update_one(
                    {'_id': aspect_ratio_id},
                    {"$set": {
                        "status": "conversion_failed",
                        "conversion_end_time": datetime.datetime.now(),
                    }}
                )

                return AppResponse(
                    status="error",
                    error={
                        "aspect_ratio_id": aspect_ratio_id,
                        "message": f"Asset conversion failed after {MAX_CONVERSION_ATTEMPTS} attempts"
                    }
                )

            video_request_aspect_ratios_collection.update_one(
                {'_id': aspect_ratio_id},
                {"$inc": {"conversion_attempts": 1},
                 "$set": {
                    "status": "requested",
                    "conversion_end_time": datetime.datetime.now(),
                }}
            )

        return AppResponse(
            status="error",
            error={"aspect_ratio_id": aspect_ratio_id, "message": str(e)}
        )


def fetch_next_aspect_ratio_for_asset_conversion():
    # first find request_ids where all uploads are in status description_complete
    excluded_request_ids = uploads_collection.distinct(
        "request_id",
        {
            "status": {"$nin": ["description_complete"]}
        }
    )
    aspect_ratio_result = video_request_aspect_ratios_collection.find_one_and_update(
        {
            "status": "requested",
            "conversion_attempts": {"$lt": MAX_CONVERSION_ATTEMPTS},
            "request_id": {"$nin": excluded_request_ids}
        },
        {
            "$set": {
                "conversion_start_time": datetime.datetime.now(),
                "conversion_end_time": None,
                "status": "conversion_started"
            }
        },
        sort=[("_id", pymongo.ASCENDING)],
        return_document=pymongo.ReturnDocument.AFTER
    )

    if aspect_ratio_result:
        return AppResponse(
            status="success",
            data={"aspect_ratio_id": aspect_ratio_result["_id"]}
        )
    else:
        return AppResponse(
            status="success",
            data={"aspect_ratio_id": None,
                  "message": "No video request format found"}
        )


async def find_and_convert_aspect_ratios(max_count=None, batch_size=1):
    processed_count = 0
    while True:
        try:
            batch = []
            remaining_count = max_count - processed_count if max_count is not None else batch_size
            for _ in range(min(batch_size, remaining_count)):
                fetch_next_aspect_ratio_result = fetch_next_aspect_ratio_for_asset_conversion()
                if fetch_next_aspect_ratio_result.status == "success" and fetch_next_aspect_ratio_result.data["aspect_ratio_id"]:
                    batch.append(
                        fetch_next_aspect_ratio_result.data["aspect_ratio_id"])
                else:
                    break

            if not batch:
                # Wait for a short time if no assets are found
                logger.info(
                    f"No uploads found. Sleeping for {NO_ASPECT_RATIOS_WAIT_SECONDS} seconds.")
                await asyncio.sleep(NO_ASPECT_RATIOS_WAIT_SECONDS)
                continue

            results = await asyncio.gather(*[convert_uploads_to_aspect_ratio(aspect_ratio_id) for aspect_ratio_id in batch])

            for result in results:
                if result.status == "error":
                    logger.error(result)
                    logger.error(
                        f"Failed to describe upload {result.error['upload_id']}: {result.error['message']}")

            processed_count += len(batch)
            if max_count is not None and processed_count >= max_count:
                break

        except Exception as e:
            logger.error(f"An exception occurred: {e}")
