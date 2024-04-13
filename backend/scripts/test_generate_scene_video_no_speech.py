import asyncio
import argparse
import sys
import os

# Add the project's root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.video.generate_scene_video import generate_scene_body_video
from lib.database import get_db_connection
from models.scene import Scene
from models.video import Video

_client, db = get_db_connection()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a video without speech")
    parser.add_argument("scene_id", help="Scene id.")
    parser.add_argument("--subtitles", action="store_true",
                        help="Add subtitles to the video if present.")
    parser.add_argument("--narrate", action="store_true",
                        help="Add narration audio to the video if present.")

    args = parser.parse_args()

    scene = Scene(**db.scenes.find_one({"_id": args.scene_id}))
    video = Video(**db.videos.find_one({"_id": scene.video_id}))

    asyncio.run(generate_scene_body_video(
        video, scene,
        add_subtitles=args.subtitles,
        add_narration=args.narrate
    ))
