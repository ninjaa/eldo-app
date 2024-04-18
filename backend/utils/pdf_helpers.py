import os
import requests
from constants import PDF_DOWNLOAD_FOLDER
# from pdf2image import convert_from_path
# from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError
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


# def convert_pdf_to_png(folder_images, pdf_file_path, arxiv_name):
#     try:
#         # Create a folder for storing the PNGs
#         sub_folder_name = os.path.splitext(
#             os.path.basename(pdf_file_path))[0] + "_pngs"
#         full_path = os.path.join(folder_images, sub_folder_name)
#         if not os.path.exists(full_path):
#             os.makedirs(full_path)

#         # Convert each page of the PDF to PNG
#         images = convert_from_path(pdf_file_path, output_folder=full_path)
#         # arxiv_name = sub_folder_name.replace("_pngs", "")

#         # Save each image as a separate PNG file
#         for i, image in enumerate(images):
#             png_path = os.path.join(
#                 full_path, f"{arxiv_name}_page_{i + 1}.png")
#             image.save(png_path, "PNG")

#         print(f"\nAll pages converted and saved in the folder: {full_path}")

#         # Clean up: Delete the .ppm files and uncropped files
#         for filename in os.listdir(full_path):
#             if filename.endswith(".ppm"):
#                 file_to_remove_path = os.path.join(full_path, filename)
#                 os.remove(file_to_remove_path)

#         print(f"\n.ppm artifacts deleted in the folder: {full_path}")
#     except Exception as e:
#         print(f"\nError: {e}")
#         print(f"Skipping processing of {pdf_file_path}")
