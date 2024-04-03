
import argparse
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.describe_uploads import find_and_describe_uploads


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Process uploads with a maximum count.')
    parser.add_argument('--max-count', type=int, default=None,
                        help='Maximum number of uploads to process')
    parser.add_argument('--batch-size', type=int, default=3,
                        help='Number of uploads to process in parallel')

    args = parser.parse_args()

    asyncio.run(find_and_describe_uploads(
        max_count=args.max_count, batch_size=args.batch_size))
