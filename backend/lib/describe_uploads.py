import asyncio
import pymongo
import datetime
from models.app_response import AppResponse
from models.upload import Upload
from utils.video.transcribe import extract_transcript_from_deepgram, is_transcript_usable, tidy_transcript
from utils.video.video_helpers import extract_and_describe_frames, summarize_description, get_video_size
from utils.image.image_helpers import (
    detect_aspect_ratio,
    describe_image,
    detect_image_size_and_aspect_ratio,
    is_image_logo,
    is_image_profile_pic
)
from moviepy.editor import VideoFileClip
from lib.database import get_db_connection
from lib.logger import setup_logger

logger = setup_logger(__name__)

_client, db = get_db_connection()
uploads_collection = db.uploads

MAX_DESCRIPTION_ATTEMPTS = 3
NO_UPLOADS_WAIT_SECONDS = 5


async def describe_upload(upload_id: str):
    try:
        # Find the upload by its ID
        uploads_result = uploads_collection.find_one({"_id": upload_id})
        # breakpoint()
        upload = Upload(**uploads_result)

        if upload:
            long_description = ""
            if upload.content_type.startswith("video"):
                logger.info(
                    f"Describing upload {upload_id} with filename {upload.filename}")
                clip = VideoFileClip(upload.file_path)
                duration = clip.duration

                transcript_task = extract_transcript_from_deepgram(
                    upload.file_path, upload.content_type)
                frames_task = extract_and_describe_frames(
                    upload.file_path, interval=4)

                raw_transcript, long_description = await asyncio.gather(transcript_task, frames_task)

                description = summarize_description(
                    long_description, raw_transcript, duration)
                if not description:  # b/c sometimes summary fails so just overwrite desc with raw_desc
                    description = long_description

                has_speech = len(raw_transcript) > 7 and is_transcript_usable(
                    raw_transcript)

                if has_speech:
                    transcript = tidy_transcript(
                        description, raw_transcript, duration)
                else:
                    raw_transcript = ""
                    transcript = ""

                video_width, video_height = get_video_size(upload.file_path)
                video_aspect_ratio = detect_aspect_ratio(
                    video_width, video_height)
                video_fps = clip.fps

                # Update the asset description
                uploads_collection.update_one(
                    {"_id": upload_id},
                    {"$set": {
                        "description": description,
                        "has_speech": has_speech,
                        "transcript": transcript,
                        "metadata.duration": duration,
                        "metadata.width": video_width,
                        "metadata.height": video_height,
                        "metadata.aspect_ratio": video_aspect_ratio,
                        "metadata.fps": video_fps,
                        "description_end_time": datetime.datetime.now(),
                        "status": "description_complete"
                    }}
                )

            if upload.content_type.startswith("image"):
                logger.info(
                    f"Describing image upload {upload_id} with filename {upload.filename}")
                description_task = describe_image(
                    upload.file_path, f"filename is ${upload.filename}")

                is_logo_task = is_image_logo(upload.file_path)
                is_profile_pic_task = is_image_profile_pic(upload.file_path)

                description, is_logo, is_profile_pic = await asyncio.gather(description_task, is_logo_task, is_profile_pic_task)

                image_width, image_height, aspect_ratio = detect_image_size_and_aspect_ratio(
                    upload.file_path)

                # Update the asset description
                uploads_collection.update_one(
                    {"_id": upload_id},
                    {"$set": {
                        "description": description,
                        "metadata.width": image_width,
                        "metadata.height": image_height,
                        "metadata.aspect_ratio": aspect_ratio,
                        "metadata.is_logo": is_logo,
                        "metadata.is_profile_pic": is_profile_pic,
                        "description_end_time": datetime.datetime.now(),
                        "status": "description_complete"
                    }}
                )

            return AppResponse(
                status="success",
                data={
                    "upload_id": upload_id,
                    "message": "Asset description updated successfully"
                }
            )
        else:
            return AppResponse(
                status="error",
                error={
                    "upload_id": upload_id,
                    "message": "Asset not found"
                }
            )
    except Exception as e:
        upload = uploads_collection.find_one({"_id": upload_id})
        if upload["description_attempts"] + 1 >= MAX_DESCRIPTION_ATTEMPTS:
            uploads_collection.update_one(
                {"_id": upload_id},
                {"$set": {
                    "status": "description_failed",
                    "description_end_time": datetime.datetime.now(),
                }}
            )
            return AppResponse(
                status="error",
                error={
                    "upload_id": upload_id,
                    "message": f"Asset description failed after {MAX_DESCRIPTION_ATTEMPTS} attempts"
                }
            )
        else:
            uploads_collection.update_one(
                {"_id": upload_id},
                {"$inc": {"description_attempts": 1},
                 "$set": {"status": "uploaded"}}
            )
            return AppResponse(
                status="error",
                error={
                    "": upload_id,
                    "message": f"An exception occurred: {e}"
                }
            )


def fetch_next_upload_for_description():
    upload = uploads_collection.find_one_and_update(
        {
            "status": "uploaded",
            "description_attempts": {"$lt": MAX_DESCRIPTION_ATTEMPTS},
        },
        {
            "$set": {
                "description_start_time": datetime.datetime.now(),
                "description_end_time": None,
                "status": "description_started"
            }
        },
        sort=[("_id", pymongo.ASCENDING)],
        return_document=pymongo.ReturnDocument.AFTER
    )

    if upload:
        return AppResponse(
            status="success",
            data={"upload_id": upload["_id"]}
        )
    else:
        return AppResponse(
            status="success",
            data={"upload_id": None, "message": "No upload found"}
        )


async def find_and_describe_uploads(max_count=None, batch_size=1):
    processed_count = 0
    while True:
        try:
            batch = []
            remaining_count = max_count - processed_count if max_count is not None else batch_size
            for _ in range(min(batch_size, remaining_count)):
                fetch_next_upload_result = fetch_next_upload_for_description()
                upload_id = fetch_next_upload_result.data['upload_id']
                if fetch_next_upload_result.status == "success" and upload_id:
                    batch.append(upload_id)
                else:
                    break

            if not batch:
                # Wait for a short time if no assets are found
                logger.info(
                    f"No uploads found. Sleeping for {NO_UPLOADS_WAIT_SECONDS} seconds.")
                await asyncio.sleep(NO_UPLOADS_WAIT_SECONDS)
                continue

            results = await asyncio.gather(*[describe_upload(upload_id) for upload_id in batch])

            for result in results:
                if result.status == "error":
                    logger.error(
                        f"Failed to describe upload {result.error['upload_id']}: {result.error['message']}")

            processed_count += len(batch)
            if max_count is not None and processed_count >= max_count:
                break

        except Exception as e:
            logger.error(f"An exception occurred: {e}")
