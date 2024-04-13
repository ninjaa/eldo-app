from constants import UPLOAD_DIRECTORY
import subprocess
import asyncio
import datetime
import pymongo
from lib.database import get_db_connection
from lib.logger import setup_logger
from models.app_response import AppResponse
from models.scene import Scene as DbScene
from utils.exception_helpers import log_exception
import os
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)
_client, db = get_db_connection()

scenes_collection = db.scenes

MAX_SCENE_NARRATION_ATTEMPTS = 3
NO_SCENES_WAIT_SECONDS = 5


async def narrate_scene(scene_id, change_status=True):
    scene_result = scenes_collection.find_one_and_update(
        {"_id": scene_id},
        {"$set": {
            "status": "narration_started",
            "scene_narration_start_time": datetime.datetime.now(),
            "scene_narration_end_time": None,
            "scene_narration_duration": None
        }},
        sort=[("_id", pymongo.ASCENDING)],
        return_document=pymongo.ReturnDocument.AFTER
    )
    scene = DbScene(**scene_result)
    try:
        # Generate the output directory for scene narrations
        narrations_directory_path = os.path.join(
            UPLOAD_DIRECTORY, scene.request_id, scene.aspect_ratio, "scene_narrations")
        os.makedirs(narrations_directory_path, exist_ok=True)

        # Escape the narration text
        escaped_narration_text = scene.narration.replace(
            "'", "").replace('"', '')

        # Generate the output filename
        audio_filename = f"scene_{scene.id}.mp3"
        output_path = os.path.join(narrations_directory_path, audio_filename)

        # Send the scene narration to ElevenLabs for text-to-speech
        curl_command = f'curl --request POST '\
                       f'--url https://api.elevenlabs.io/v1/text-to-speech/nPczCjzI2devNBz1zQrb '\
                       f'--header "Content-Type: application/json" '\
                       f'--header "xi-api-key: {os.getenv("ELEVENLABS_API_KEY")}" '\
                       f'--data \'{{ '\
                       f'"model_id": "eleven_turbo_v2", '\
                       f'"text": "{escaped_narration_text}", '\
                       f'"voice_settings": {{ '\
                       f'"similarity_boost": 0.75, '\
                       f'"stability": 0.3, '\
                       f'"use_speaker_boost": true '\
                       f'}} '\
                       f'}}\' -o "{output_path}"'

        subprocess.run(curl_command, shell=True)

        # Get the duration of the generated MP3 using ffprobe
        ffprobe_command = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{output_path}"'
        duration_output = subprocess.check_output(
            ffprobe_command, shell=True).decode().strip()

        duration = float(duration_output)

        scene_narration_end_time = datetime.datetime.now()
        scene_narration_duration = (
            scene_narration_end_time - scene.scene_narration_start_time).total_seconds()
        
        scenes_collection.update_one(
            {"_id": scene_id},
            {
                "$set": {
                    "status": "narration_complete",
                    "scene_narration_end_time": scene_narration_end_time,
                    "scene_narration_duration": scene_narration_duration,
                    "narration_audio_filename": audio_filename,
                    "duration": duration
                },
                "$inc": {"scene_narration_attempts": 1}
            }
        )
        return AppResponse(
            status="success",
            data={
                "message": f"Success narrating scene {scene_id}",
                "scene_id": scene_id,
                "audio_filename": audio_filename,
                "duration": duration
            }
        )
    except Exception as e:
        scenes_collection.update_one(
            {"_id": scene_id},
            {
                "$set": {
                    "status": "scene_narration_failed"
                },
                "$inc": {"scene_narration_attempts": 1}
            }
        )
        log_exception(logger, e)
        return AppResponse(
            status="error",
            error={
                "message": f"Error narrating scene {scene_id}",
                "scene_id": scene_id
            }
        )


def fetch_next_scene_for_narration(change_status=True):
    if change_status:
        scene_result = scenes_collection.find_one_and_update(
            {
                "status": "generated",
                "scene_narration_attempts": {"$lt": MAX_SCENE_NARRATION_ATTEMPTS},
            },
            {
                "$set": {
                    "scene_narration_start_time": datetime.datetime.now(),
                    "scene_narration_end_time": None,
                    "status": "narration_queued"
                },
                "$inc": {"scene_narration_attempts": 1}
            },
            sort=[("_id", pymongo.ASCENDING)],
            return_document=pymongo.ReturnDocument.AFTER
        )
    else:
        scene_result = scenes_collection.find_one({
            "status": "generated",
            "scene_narration_attempts": {"$lt": MAX_SCENE_NARRATION_ATTEMPTS}
        },
            sort=[("_id", pymongo.ASCENDING)],
            return_document=pymongo.ReturnDocument.AFTER)

    if scene_result:
        return AppResponse(
            status="success",
            data={"scene_id": scene_result["_id"]}
        )
    else:
        return AppResponse(
            status="success",
            data={"scene_id": None,
                  "message": "No scene found for narration"}
        )


async def find_scenes_and_narrate(max_count=None, batch_size=1, change_status=True):
    processed_count = 0
    while True:
        try:
            batch = []
            remaining_count = max_count - processed_count if max_count else float('inf')
            for _ in range(min(batch_size, remaining_count)):
                fetch_next_scene_result = fetch_next_scene_for_narration(
                    change_status=change_status)
                scene_id = fetch_next_scene_result.data.get("scene_id")
                if scene_id:
                    batch.append(scene_id)
                else:
                    break

            if not batch:
                logger.info(
                    f"No scenes found for narration. Sleeping for {NO_SCENES_WAIT_SECONDS} seconds")
                await asyncio.sleep(NO_SCENES_WAIT_SECONDS)
                continue

            results = await asyncio.gather(*[narrate_scene(scene_id, change_status) for scene_id in batch])

            for result in results:
                if result.status == "error":
                    logger.error(
                        f"Error narrating scene {scene_id}. Error: {result.message}")

            processed_count += len(batch)
            if max_count is not None and processed_count >= max_count:
                break

        except Exception as e:
            log_exception(logger, e)
