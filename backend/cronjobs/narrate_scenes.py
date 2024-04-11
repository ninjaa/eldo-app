from pprint import pprint
import argparse
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.narrate_scenes import find_scenes_and_narrate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Narrate scenes with a maximum count.')
    parser.add_argument('--max-count', type=int, default=None,
                        help='Maximum number of scenes to narrate')
    parser.add_argument('--batch-size', type=int, default=3,
                        help='Number of scenes to process in parallel')
    parser.add_argument('--no-change-status', dest='change_status',
                        action='store_false', help='Do not change Video Request status')
    parser.set_defaults(change_status=True)
    args = parser.parse_args()

    asyncio.run(
        find_scenes_and_narrate(
            max_count=args.max_count,
            batch_size=args.batch_size,
            change_status=args.change_status
        )
    )
