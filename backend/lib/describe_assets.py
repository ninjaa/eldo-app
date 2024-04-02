
import logging
import pdb
import asyncio
import pymongo
import datetime
from lib.models import Asset
from utils.video.transcribe import extract_transcript_from_deepgram, is_transcript_usable, tidy_transcript
from utils.video.video_helpers import extract_and_describe_frames, summarize_description, get_video_size
from utils.image.image_helpers import detect_aspect_ratio, describe_image, detect_image_size_and_aspect_ratio
from moviepy.editor import VideoFileClip
from lib.database import get_db_connection

_client, _db, _videos, assets = get_db_connection()

MAX_DESCRIPTION_ATTEMPTS = 3


async def describe_asset(asset_id: str):
    try:
        # Find the asset by its ID
        assets_result = assets.find_one({"_id": asset_id})
        # breakpoint()
        asset = Asset(**assets_result)

        if asset:
            long_description = ""
            if asset.content_type.startswith("video"):
                logger.info(
                    f"Describing video asset {asset_id} with filename {asset.filename}")
                clip = VideoFileClip(asset.file_path)

                print("fetching transcription from deepgram")
                raw_transcript = extract_transcript_from_deepgram(
                    asset.file_path, asset.content_type)
                duration = clip.duration
                long_description = extract_and_describe_frames(
                    asset.file_path, interval=4)
                has_speech = len(raw_transcript) > 7 and is_transcript_usable(
                    raw_transcript)
                if has_speech:
                    transcript = tidy_transcript(
                        description, raw_transcript, duration)
                else:
                    raw_transcript = ""
                    transcript = ""

                description = summarize_description(
                    long_description, raw_transcript, duration)
                if not description:  # b/c sometimes summary fails so just overwrite desc with raw_desc
                    description = long_description

                video_width, video_height = get_video_size(asset.file_path)
                video_aspect_ratio = detect_aspect_ratio(
                    video_width, video_height)
                video_fps = clip.fps

                # Update the asset description
                assets.update_one(
                    {"_id": asset_id},
                    {"$set": {
                        "description": description,
                        "has_speech": has_speech,
                        "transcript": transcript,
                        "metadata.duration": duration,
                        "metadata.width": video_width,
                        "metadata.height": video_height,
                        "metadata.aspect_ratio": video_aspect_ratio,
                        "metadata.fps": video_fps,
                        "status": "description_complete"
                    }}
                )

            if asset.content_type.startswith("image"):
                logger.info(
                    f"Describing image asset {asset_id} with filename {asset.filename}")
                description = describe_image(
                    asset.file_path, f"filename is ${asset.filename}")

                image_width, image_height, aspect_ratio = detect_image_size_and_aspect_ratio(
                    asset.file_path)

                # Update the asset description
                assets.update_one(
                    {"_id": asset_id},
                    {"$set": {
                        "description": description,
                        "metadata.width": image_width,
                        "metadata.height": image_height,
                        "metadata.aspect_ratio": aspect_ratio,
                        "status": "description_complete"
                    }}
                )

            return {"asset_id": asset_id, "message": "Asset description updated successfully"}
        else:
            return {"asset_id": asset_id, "message": "Asset not found"}
    except Exception as e:
        asset = assets.find_one({"_id": asset_id})
        if asset["description_attempts"] + 1 >= MAX_DESCRIPTION_ATTEMPTS:
            assets.update_one(
                {"_id": asset_id},
                {"$set": {"status": "description_failed"}}
            )
            return {"asset_id": asset_id, "message": f"Asset description failed after {MAX_DESCRIPTION_ATTEMPTS} attempts"}
        else:
            assets.update_one(
                {"_id": asset_id},
                {"$inc": {"description_attempts": 1},
                 "$set": {"status": "uploaded"}}
            )
            return {"asset_id": asset_id, "message": f"An exception occurred: {e}"}


def fetch_next_asset_for_description():
    asset = assets.find_one_and_update(
        {
            "status": "uploaded",
            "description_attempts": {"$lt": MAX_DESCRIPTION_ATTEMPTS},
        },
        {
            "$set": {
                "asset_processing_start_time": datetime.datetime.now(),
                "asset_processing_end_time": None,
                "status": "description_started"
            }
        },
        sort=[("_id", pymongo.ASCENDING)],
        return_document=pymongo.ReturnDocument.AFTER
    )

    if asset:
        return {"asset_id": asset["_id"]}
    else:
        return {"message": "No asset found"}


NO_ASSETS_WAIT_SECONDS = 5


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def find_and_describe_assets(max_count=None, batch_size=1):
    processed_count = 0
    while True:
        try:
            batch = []
            for _ in range(batch_size):
                asset = fetch_next_asset_for_description()
                if 'asset_id' in asset:
                    batch.append(asset['asset_id'])
                else:
                    break

            if not batch:
                # Wait for a short time if no assets are found
                logger.info(
                    f"No assets found. Sleeping for {NO_ASSETS_WAIT_SECONDS} seconds.")
                await asyncio.sleep(NO_ASSETS_WAIT_SECONDS)
                continue

            results = await asyncio.gather(*[describe_asset(asset_id) for asset_id in batch])

            for result in results:
                if "message" in result and "Asset description updated successfully" not in result["message"]:
                    print(
                        f"Failed to describe asset {result['asset_id']}: {result['message']}")

            processed_count += len(batch)
            if max_count is not None and processed_count >= max_count:
                break

        except Exception as e:
            print(f"An exception occurred: {e}")
