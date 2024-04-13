import argparse
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.process_scenes import fetch_and_process_videos

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generates video by processing scenes.')
    parser.add_argument("--regenerate", action="store_true",
                        help="Force regeneration of all scenes.")

    args = parser.parse_args()

    asyncio.run(fetch_and_process_videos(force_regenerate=args.regenerate))
