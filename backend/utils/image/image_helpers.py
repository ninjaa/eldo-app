from PIL import Image
import anthropic
import base64
import magic
import math
from dotenv import load_dotenv

load_dotenv()


def detect_aspect_ratio(image_width, image_height):
    # Calculate the greatest common divisor (GCD) of the width and height
    gcd = math.gcd(image_width, image_height)

    # Calculate the aspect ratio
    aspect_ratio = f"{image_width // gcd}:{image_height // gcd}"

    return aspect_ratio


async def describe_image(image_path, additional_context=""):
    client = anthropic.Anthropic()

    # Read the image file from the local path
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # Determine the media type based on the file extension
    media_type = magic.from_file(image_path, mime=True)

    # Encode the image data as base64
    encoded_image = base64.b64encode(image_data).decode("utf-8")

    prompt = "Describe this image very succinctly but descriptively for a TV news / social media script. Feel free to use keywords and clipped language. Almost like a prompt for image generation. " + \
        additional_context

    # Create the message for the Anthropic API
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        system="You are a video editor and you are helping a user edit a video.",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    # Extract the image description from the API response
    description = message.content[0].text

    return description


async def is_image_logo(image_path):
    client = anthropic.Anthropic()

    # Read the image file from the local path
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # Determine the media type based on the file extension
    media_type = magic.from_file(image_path, mime=True)

    # Encode the image data as base64
    encoded_image = base64.b64encode(image_data).decode("utf-8")

    prompt = "Is this image a logo? Please respond with just 'Yes' or 'No'."

    # Create the message for the Anthropic API
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        system="You are an image analysis assistant.",
        max_tokens=10,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encoded_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    # Extract the logo detection result from the API response
    is_logo = message.content[0].text.strip().lower() == "yes"

    return is_logo


def detect_image_size_and_aspect_ratio(image_path):
    # Load the image
    image = Image.open(image_path)

    # Get the current image dimensions
    image_width, image_height = image.size

    aspect_ratio = detect_aspect_ratio(image_width, image_height)

    return image_width, image_height, aspect_ratio
