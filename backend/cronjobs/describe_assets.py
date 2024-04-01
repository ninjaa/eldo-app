
import asyncio
from pprint import pprint

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.describe_assets import find_and_describe_assets

if __name__ == "__main__":
    asyncio.run(find_and_describe_assets(count=1))
