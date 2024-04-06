from pprint import pprint
import argparse
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.extract_scenes import find_scripted_videos_and_extract_scenes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Process assets with a maximum count.')
    parser.add_argument('--max-count', type=int, default=None,
                        help='Maximum number of assets to process')
    parser.add_argument('--batch-size', type=int, default=3,
                        help='Number of assets to process in parallel')
    parser.add_argument('--no-change-status', dest='change_status',
                        action='store_false', help='Do not change Video Request status')
    parser.set_defaults(change_status=True)
    args = parser.parse_args()

    asyncio.run(
        find_scripted_videos_and_extract_scenes(
            max_count=args.max_count,
            batch_size=args.batch_size,
            change_status=args.change_status
        )
    )
