from PIL import Image
import os
import requests
from constants import PDF_DOWNLOAD_FOLDER
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
from utils.helpers import slugify
from urllib.parse import urlparse, unquote


def download_and_save_pdf(url, download_folder=PDF_DOWNLOAD_FOLDER):
    """
    Download and save a PDF file from a URL into a local directory, creating a subdirectory
    for the PDF based on its name, slugified.

    Parameters:
    - url (str): The URL of the PDF.

    Returns:
    - str: Path of the downloaded PDF if successful, or an error message.
    """
    try:
        # Extract the PDF name from the URL
        pdf_name = os.path.basename(unquote(urlparse(url).path))
        # Slugify the PDF name to create a safe directory name
        pdf_slugified_name = slugify(pdf_name)

        # Create the directory path
        pdf_dir_path = os.path.join(download_folder, pdf_slugified_name)
        os.makedirs(pdf_dir_path, exist_ok=True)

        # Define the full path for the PDF file
        pdf_file_path = os.path.join(pdf_dir_path, pdf_name)

        # Download the PDF
        response = requests.get(url)
        if response.status_code == 200:
            with open(pdf_file_path, 'wb') as pdf_file:
                pdf_file.write(response.content)
            return pdf_file_path
        else:
            return "Error: Failed to download PDF."
    except Exception as e:
        return f"Error: {e}"


def convert_pdf_to_png(pdf_path, images_folder=None, do_cut_pngs_in_half=True):
    """
    Convert a PDF file to PNG images, saving the images in a specified directory.

    Parameters:
    - pdf_path: Path to the PDF file.
    - images_folder: Directory to save the images. If None, saves in a subdirectory 'images' under the PDF's directory.
    """
    # Determine the images output directory
    if images_folder is None:
        base_dir = os.path.dirname(pdf_path)
        images_folder = os.path.join(base_dir, "images")

    # Ensure the images directory exists
    if not os.path.exists(images_folder):
        os.makedirs(images_folder)

    try:
        # Convert PDF to a list of image objects
        images = convert_from_path(pdf_path)

        # Save each page as an image in the specified directory
        for i, image in enumerate(images):
            image_path = os.path.join(images_folder, f"page_{i+1}.png")
            image.save(image_path, 'PNG')
            print(f"Saved: {image_path}")
    except Exception as e:
        print(f"Error converting PDF to PNG: {e}")
        
    if do_cut_pngs_in_half:
        cut_pngs_in_half(images_folder)
        
    return images_folder


def cut_pngs_in_half(image_folder):
    # Ensure the directory path is valid
    if not os.path.exists(image_folder):
        print(f"\nError: Directory '{image_folder}' does not exist.")
        return

    # Get a list of all files in the directory
    files = [f for f in os.listdir(image_folder) if os.path.isfile(
        os.path.join(image_folder, f))]

    # Process each file in the directory
    for file_name in files:
        # Check if the file is a PNG and does not contain 'cropped' in the name
        if file_name.lower().endswith('.png') and 'cropped' not in file_name.lower():
            image_path = os.path.join(image_folder, file_name)

            # Open the image
            with Image.open(image_path) as img:
                # Get the dimensions of the image
                width, height = img.size

                # Cut the image in half (top and bottom)
                top_half = img.crop((0, 0, width, height // 2))
                bottom_half = img.crop((0, height // 2, width, height))

                # Save the top and bottom halves with "_cropped_1" and "_cropped_2" suffixes
                top_half.save(os.path.join(
                    image_folder, f"{os.path.splitext(file_name)[0]}_cropped_1.png"), 'PNG')
                bottom_half.save(os.path.join(
                    image_folder, f"{os.path.splitext(file_name)[0]}_cropped_2.png"), 'PNG')

                print(
                    f"\nImages saved: {file_name}_cropped_1.png (top) and {file_name}_cropped_2.png (bottom)")
        else:
            print(
                f"\nSkipping processing for {file_name} as it contains 'cropped' in the file name.")
