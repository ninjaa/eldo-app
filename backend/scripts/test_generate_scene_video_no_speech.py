import asyncio
import argparse
import sys
import os

# Add the project's root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.video import Video
from models.scene import Scene
from lib.database import get_db_connection
from utils.video.generate_scene_video import generate_scene_video_no_speech

_client, db = get_db_connection()

# example usage python scripts/convert_image_to_aspect_ratio.py ./media/multion-example/20240323_181051.jpg ./media/20240323_181051_9_16_contain.jpg 9 16 --crop_type contain --background_color 0 0 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a video without speech")
    parser.add_argument("scene_id", help="Scene id.")
    parser.add_argument("--subtitles", action="store_true",
                        help="Add subtitles to the video if present.")

    args = parser.parse_args()

    scene = Scene(**db.scenes.find_one({"_id": args.scene_id}))
    video = Video(**db.videos.find_one({"_id": scene.video_id}))

    asyncio.run(generate_scene_video_no_speech(
        video, scene, add_subtitles=args.subtitles))
