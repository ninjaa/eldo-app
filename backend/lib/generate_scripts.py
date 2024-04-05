from bson.objectid import ObjectId
import asyncio
import datetime
import math
import openai
import os
import pymongo
from dotenv import load_dotenv
from typing import List
from lib.database import get_db_connection
from lib.logger import setup_logger
from models.asset import Asset
from models.app_response import AppResponse
from models.video import Video
from utils.json_helpers import clean_json, extract_json

load_dotenv()
logger = setup_logger(__name__)

NO_VIDEO_SCRIPTS_WAIT_SECONDS = 5
MAX_GENERATION_ATTEMPTS = 3

_client, db = get_db_connection()
videos_collection = db.videos
assets_collection = db.assets


def generate_title_and_script(video: Video, assets: List[Asset]):
    video_json = video.model_dump_json(indent=2)
    assets_json = [asset.model_dump_json(indent=2) for asset in assets]

    api_token = os.getenv("MISTRAL_API_KEY")
    client = openai.OpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key=api_token
    )

    number_of_words = math.ceil(2.5 * video.length)

    if video.aspect_ratio == "16x9":
        video_format = "YouTube"
    elif video.aspect_ratio == "1x1":
        video_format = "Instagram"
    elif video.aspect_ratio == "9x16":
        video_format = "TikTok"
    else:
        video_format = ""

    prompt = f"""
    You're an expert AI video editor and you're tasked with generating a title and script for a social media video for a big brand.
    
    Please refer to what the company does and also to the setting. 
    
    Please be very explicit about the city and the landmarks and other distinctive features as we will generate content and search stock databases using keywords mined from the script.
    
    Please include Narrator (Voiceover) as well as Cut to: in the script. If there's testimonials or any other videos with speech in the assets, you can Cut to: those as well, refer to the filename or type.
    
    Please keep the script to under {number_of_words} words this is for a {video.length} second {video_format} {video.style}.
    
    The spec for the video to edit is as follows:
    {video_json}

    The assets to use are as follows:
    {assets_json}
    
    Please provide your title and script as JSON in the following format
    
        {{ 
        "title" : "some title for a compelling video", 
        "script" : "some script for a compelling video"
        }}
    
    """

    print(prompt)

    chat_completion = client.chat.completions.create(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": "You are a video editor screenwriting and then cutting a TV news / social media video."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=1000
    )

    answer = chat_completion.choices[0].message.content.strip()
    print(f"what we got from generate_title_and_script: {answer}")
    return answer


async def generate_script(video_id, change_status=True):
    video = Video(**videos_collection.find_one({"_id": video_id}))
    asset_dicts = list(assets_collection.find(
        {
            "status": "converted",
            "request_id": video.request_id,
            "metadata.aspect_ratio": video.aspect_ratio
        }))
    assets = [Asset(**asset_dict) for asset_dict in asset_dicts]
    print(assets)
    print(video)
    if video and len(assets) > 0:
        try:
            text = generate_title_and_script(video, assets)
        except Exception as e:
            logger.error(f"Error generating script for video {video_id}: {e}")
            return AppResponse(
                status="error",
                message=f"Error generating script for video {video_id}: {e}"
            )


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
