import argparse
import sys
import os

# Add the project's root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.pdf_helpers import download_and_save_pdf, convert_pdf_to_png
from constants import PDF_DOWNLOAD_FOLDER

# example usage python scripts/convert_pdf_to_images.py https://arxiv.org/pdf/2404.10636.pdf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a pdf to a set of screenshots.")
    parser.add_argument("url", help="Url to remote pdf.")

    args = parser.parse_args()

    pdf_path = download_and_save_pdf(args.url, PDF_DOWNLOAD_FOLDER)
    convert_pdf_to_png(pdf_path)
