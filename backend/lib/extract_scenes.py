# for each next 'requested' format
# we will check that all media uploads are in description_complete status
# for each upload
# convert to format aspect ratio
# if all uploads have been converted to the aspect ratio within, we will update the status of the video_request_format to "converted"

from models.asset import Asset
from typing import Optional
from constants import UPLOAD_DIRECTORY
import asyncio
import datetime
import os
import pymongo
from lib.database import get_db_connection
from lib.logger import setup_logger
from models.app_response import AppResponse
from models.scene import Scene as DbScene
from models.video import Video
from bson.objectid import ObjectId
from utils.exception_helpers import log_exception

from pydantic import BaseModel, Field
from typing import List
import instructor
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)
_client, db = get_db_connection()

videos_collection = db.videos
scenes_collection = db.scenes
assets_collection = db.assets

# This enables response_model keyword
# from client.chat.completions.create
client = instructor.patch(OpenAI())

MAX_SCENE_EXTRACTION_ATTEMPTS = 3
NO_SCRIPTS_WAIT_SECONDS = 5


class Scene(BaseModel):
    """The object representing a scene in the event video"""
    narration: str = Field(description="Narration or voiceover for the scene")
    asset_filenames: List[str] = Field(
        description="Filename of the associated asset (image or video) for the scene, if applicable", default=None)


class EventVideo(BaseModel):
    """The format of the event video."""
    title: str = Field(description="Title of the event video")
    scenes: List[Scene] = Field(
        description="List of scenes in the event video (starts with Cut to), including the title scene and outro scene")


def generate_scenes_with_llm(video: Video, assets: List[Asset]):
    assets_json = [asset.model_dump_json(indent=2) for asset in assets]
    prompt = f"""
Generate scenes for a {video.length} second {video.video_format} {video.style} based on the following script:

Use Cut to: as a marker for a new scene or a new Narrator: block
title: {video.title}
script: 
{video.script}

all available assets:
{assets_json}

Each scene should have a narration and an optional list of asset_filenames if mentioned in the script. That piece of media will be shown with the narration.

If the asset has_speech, make the associated narration short as it will go on a title slide. 

Feel free to split the narration into multiple scenes if it is too long, as long as is coherent and informative.

FEEL FREE TO CHANGE THE NARRATION TO MATCH THE GUIDELINES. BUT DO REMEMBER NOT TO MAKE THE NARRATION A PURE DESCRIPTION BUT PART OF THE STORY.

KEEP THE COHERENT STORY ARC IN MIND.

So, for example


Narrator (Voiceover): The secret sauce? A tokenizer expanded to 128,000 tokens, slashing token count by 15%. This isn't just an upgrade; it's a revolution in efficiency. Cut to: 'mark-zuckerberg-yann-lecun-meta-ai-image-9x16.webp', featuring Mark Zuckerberg and Yann LeCun, the brilliant minds propelling this innovation.

=> can yield 
asset_filenames: [mark-zuckerberg-yann-lecun-meta-ai-image-9x16.webp, facebook-meta-ai-image-9x16.webp]
narration: "Mark Zuckerberg and Yann LeCun, the brilliant minds propelling this innovation. The secret sauce? A tokenizer expanded to 128,000 tokens, slashing token count by 15%. This isn't just an upgrade; it's a revolution in efficiency."

Or
Narrator (Voiceover): But there's more - the introduction of Grouped Query Attention across all models, a game-changer in optimizing AI performance. Cut to: 'karpathy-profile-pic-image-9x16.webp', as Andrej Karpathy shares his insights on this architectural marvel.
=> 

asset_filenames: [karpathy-profile-pic-image-9x16.webp]
narration: "Andrej Karpathy shares his insights on this architectural marvel, mentioning the introduction of Grouped Query Attention across all models, a game-changer in optimizing AI performance."

And
something like 
Narrator (Voiceover): Imagine a world where AI understands us better than ever before. That's the promise of Llama 3, with its 8 billion and 70 billion parameter models, and a 400 billion behemoth on the horizon. Cut to: 'Mark Zuckerberg - Llama 3, $10B Models, Caesar Augustus, & 1 GW Datacenters [bc6uFV9CJGg]-video-9x16.webm', capturing the excitement of this groundbreaking project.

=> should be split into two scenes, the first one with no asset_filename and the latter one with the video and a short narration like "Here's Mark Zuckerberg capturing the excitement" (keep it short)

Each scene should have a narration and an optional list of asset_filenames if mentioned in the script or otherwise associated from the list of assets.

"""

    print(prompt)
    event_video = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a video editor screenwriting and then cutting a TV news / social media video."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_model=EventVideo
    )

    event_video.title = video.title

    # @TODO make this a dict and make the scene_type = title. attach the logo / splash
    # Generate the title scene separately
    title_scene = Scene(narration=video.title)
    event_video.scenes.insert(0, title_scene)

    # @TODO make this a dict and make the scene_type = outro. attach the logo / splash
    outro_scene = Scene(narration="Thank you for watching!")
    event_video.scenes.append(outro_scene)

    return event_video


async def extract_scenes(video_id, change_status=True):
    video_result = videos_collection.find_one_and_update(
        {"_id": video_id},
        {"$set": {
            "status": "scene_extraction_started",
            "scene_extraction_start_time": datetime.datetime.now(),
            "scene_extraction_end_time": None,
            "scene_extraction_duration": None
        }},
        sort=[("_id", pymongo.ASCENDING)],
        return_document=pymongo.ReturnDocument.AFTER
    )
    video = Video(**video_result)
    asset_dicts = list(assets_collection.find(
        {
            "status": "converted",
            "request_id": video.request_id,
            "metadata.aspect_ratio": video.aspect_ratio
        }))
    assets = [Asset(**asset_dict) for asset_dict in asset_dicts]
    try:
        event_video_obj = generate_scenes_with_llm(video, assets)
        scenes_collection.delete_many({"video_id": video_id})
        scenes = []
        for index, scene in enumerate(event_video_obj.scenes):
            if index == 0:
                scene_type = "title"
            elif index == len(event_video_obj.scenes) - 1:
                scene_type = "outro"
            else:
                scene_type = "body"
            new_scene_dict = {
                "id": str(ObjectId()),
                "narration": scene.narration,
                "scene_type": scene_type,
                "asset_filenames": scene.asset_filenames,
                "status": "generated",
                "video_id": video_id,
                "request_id": video.request_id,
                "aspect_ratio": video.aspect_ratio
            }
            new_scene = DbScene(**new_scene_dict)
            scenes.append(new_scene.model_dump(by_alias=True))

        # Insert scenes as a doubly linked list in the scenes collection
        for i in range(len(scenes)):
            if i < len(scenes) - 1:
                # Set the next_scene_id to None for now
                scenes[i]["next_scene_id"] = None
            else:
                # Last scene has no next scene
                scenes[i]["next_scene_id"] = None

            if i > 0:
                # Set the prev_scene_id to None for now
                scenes[i]["prev_scene_id"] = None
            else:
                # First scene has no previous scene
                scenes[i]["prev_scene_id"] = None

        # Insert scenes into the scenes collection
        inserted_scenes = db.scenes.insert_many(scenes)

        # Update the next_scene_id and prev_scene_id for each scene
        for i in range(len(inserted_scenes.inserted_ids)):
            if i < len(inserted_scenes.inserted_ids) - 1:
                db.scenes.update_one(
                    {"_id": inserted_scenes.inserted_ids[i]},
                    {"$set": {
                        "next_scene_id": inserted_scenes.inserted_ids[i + 1]}}
                )

            if i > 0:
                db.scenes.update_one(
                    {"_id": inserted_scenes.inserted_ids[i]},
                    {"$set": {
                        "prev_scene_id": inserted_scenes.inserted_ids[i - 1]}}
                )

        scene_extraction_end_time = datetime.datetime.now()
        scene_extraction_duration = (
            scene_extraction_end_time - video.scene_extraction_start_time).total_seconds()
        videos_collection.update_one(
            {"_id": video_id},
            {
                "$set": {
                    "status": "scene_extraction_complete",
                    "scene_extraction_end_time": scene_extraction_end_time,
                    "scene_extraction_duration": scene_extraction_duration
                },
                "$inc": {"scene_extraction_attempts": 1}
            }
        )
        return AppResponse(
            status="success",
            data={
                "message": f"Success extracting scenes from video {video_id}",
                "video_id": video_id
            }
        )
    except Exception as e:
        videos_collection.update_one(
            {"_id": video_id},
            {
                "$set": {
                    "status": "script_generation_complete"
                },
                "$inc": {"scene_extraction_attempts": 1}
            }
        )
        log_exception(logger, e)
        return AppResponse(
            status="error",
            error={
                "message": f"Error extracting scenes from video {video_id}",
                "video_id": video_id
            }
        )


def fetch_next_video_for_scene_extraction(change_status=True):
    if change_status:
        video_result = videos_collection.find_one_and_update(
            {
                "status": "script_generation_complete",
                "scene_extraction_attempts": {"$lt": MAX_SCENE_EXTRACTION_ATTEMPTS},
            },
            {
                "$set": {
                    "scene_extraction_start_time": datetime.datetime.now(),
                    "scene_extraction_end_time": None,
                    "status": "scene_extraction_queued"
                },
                "$inc": {"scene_extraction_attempts": 1}
            },
            sort=[("_id", pymongo.ASCENDING)],
            return_document=pymongo.ReturnDocument.AFTER
        )
    else:
        video_result = videos_collection.find_one({
            "status": "script_generation_complete",
            "scene_extraction_attempts": {"$lt": MAX_SCENE_EXTRACTION_ATTEMPTS}
        },
            sort=[("_id", pymongo.ASCENDING)],
            return_document=pymongo.ReturnDocument.AFTER)

    if video_result:
        return AppResponse(
            status="success",
            data={"video_id": video_result["_id"]}
        )
    else:
        return AppResponse(
            status="success",
            data={"aspect_ratio_id": None,
                  "message": "No video request format found"}
        )


async def find_scripted_videos_and_extract_scenes(max_count=None, batch_size=1, change_status=True):
    processed_count = 0
    while True:
        try:
            batch = []
            remaining_count = max_count - \
                processed_count if max_count else float('inf')
            for _ in range(min(batch_size, remaining_count)):
                fetch_next_video_result = fetch_next_video_for_scene_extraction(
                    change_status=change_status)
                video_id = fetch_next_video_result.data.get("video_id")
                if video_id:
                    batch.append(video_id)
                else:
                    break

            if not batch:
                logger.info(
                    f"No videos found for scene extraction. Sleeping for {NO_SCRIPTS_WAIT_SECONDS} seconds")
                await asyncio.sleep(NO_SCRIPTS_WAIT_SECONDS)
                continue

            results = await asyncio.gather(*[extract_scenes(video_id, change_status) for video_id in batch])

            for result in results:
                if result.status == "error":
                    logger.error(
                        f"Error extracting scenes for video {video_id}. Error: {result.message}")

            processed_count += len(batch)
            if max_count is not None and processed_count >= max_count:
                break

        except Exception as e:
            log_exception(logger, e)
