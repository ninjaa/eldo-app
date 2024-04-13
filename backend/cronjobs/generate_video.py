from pprint import pprint
import argparse
import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.process_scenes import fetch_and_process_videos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generates video by processing scenes.')
    # parser.add_argument('--max-count', type=int, default=None,
    #                     help='Maximum number of assets to process')
    # parser.add_argument('--batch-size', type=int, default=3,
    #                     help='Number of assets to process in parallel')
    # parser.add_argument('--no-change-status', dest='change_status',
    #                     action='store_false', help='Do not change Video Request status')
    # parser.add_argument('--no-insert-videos', dest='insert_videos',
    #                     action='store_false', help='Do not insert videos')
    # parser.set_defaults(change_status=True, insert_videos=True)
    args = parser.parse_args()

    asyncio.run(fetch_and_process_videos())
