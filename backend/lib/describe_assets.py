
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

import pdb

async def describe_asset(asset_id: str):
    # Find the asset by its ID
    assets_result = assets.find_one({"_id": asset_id})
    # breakpoint()
    asset = Asset(**assets_result)

    if asset:
        long_description = ""
        if asset.content_type.startswith("video"):
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
            video_aspect_ratio = detect_aspect_ratio(video_width, video_height)
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
            print("fetching description from anthropic")
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

        return {"message": "Asset description updated successfully"}
    else:
        return {"message": "Asset not found"}


def fetch_next_asset_for_description():
    asset = assets.find_one_and_update(
        {
            "status": "uploaded",
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


async def find_and_describe_assets(count=1, batch_size=1):
    for _ in range(0, count, batch_size):
        batch = []
        for _ in range(batch_size):
            asset = fetch_next_asset_for_description()
            if 'asset_id' in asset:
                batch.append(describe_asset(asset['asset_id']))
        await asyncio.gather(*batch)
