
import asyncio
import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.convert_assets import find_and_convert_aspect_ratios


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process assets with a maximum count.')
    parser.add_argument('--max-count', type=int, default=None, help='Maximum number of assets to process')
    parser.add_argument('--batch-size', type=int, default=3, help='Number of assets to process in parallel')

    args = parser.parse_args()

    asyncio.run(find_and_convert_aspect_ratios(max_count=args.max_count, batch_size=args.batch_size))