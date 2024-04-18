import argparse
import sys
import os

# Add the project's root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf_helpers import download_and_save_pdf
from constants import PDF_DOWNLOAD_FOLDER

# example usage python scripts/convert_pdf_to_images.py https://arxiv.org/pdf/2404.10636.pdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a pdf to a set of screenshots.")
    parser.add_argument("url", help="Url to remote pdf.")
    # # parser.add_argument(
    # #     "output_path", help="Path to save the output video file.")
    # # parser.add_argument("aspect_ratio_width", type=int,
    # #                     help="Width of the desired aspect ratio.")
    # # parser.add_argument("aspect_ratio_height", type=int,
    # #                     help="Height of the desired aspect ratio.")
    # # parser.add_argument("--crop-type", choices=["center", "contain"],
    # #                     default="center", help="Crop type: 'center' or 'contain' (default).")
    # # parser.add_argument("--background-color", nargs=3, type=int,
    # #                     default=[0, 0, 0], help="Background color in RGB format (default: black).")

    args = parser.parse_args()

    download_and_save_pdf(args.url, PDF_DOWNLOAD_FOLDER)
