from models.video import Video
from models.scene import Scene
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
    aspect_ratio = f"{image_width // gcd}x{image_height // gcd}"

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


async def is_image_profile_pic(image_path):
    client = anthropic.Anthropic()

    # Read the image file from the local path
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # Determine the media type based on the file extension
    media_type = magic.from_file(image_path, mime=True)

    # Encode the image data as base64
    encoded_image = base64.b64encode(image_data).decode("utf-8")

    prompt = "Is this image a profile picture or headshot of a person? Please respond with just 'Yes' or 'No'."

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

    # Extract the profile picture detection result from the API response
    is_profile_pic = message.content[0].text.strip().lower() == "yes"

    return is_profile_pic


def detect_image_size_and_aspect_ratio(image_path):
    # Load the image
    image = Image.open(image_path)

    # Get the current image dimensions
    image_width, image_height = image.size

    aspect_ratio = detect_aspect_ratio(image_width, image_height)

    return image_width, image_height, aspect_ratio


def extract_and_fill_prompts(response_text, num_images, scene_narration):
    # Split the response text into lines
    lines = response_text.strip().split('\n')

    # Filter out any empty lines or non-prompt text
    prompts = [line for line in lines if len(line) > 10]

    # Check if the number of prompts is at least num_images
    if len(prompts) >= num_images:
        return prompts[:num_images]
    else:
        required_prompts = num_images - len(prompts)
        fill_prompts = [
            f"{scene_narration}" for _ in range(required_prompts)]
        prompts.extend(fill_prompts)
        return prompts


def get_image_prompts(num_images, scene: Scene, video: Video):
    client = anthropic.Anthropic()

    prompt = f"""
        Given the following scene, you need to generate a list of image prompts.
        The image prompts should be based on the narration of the scene.
        
        {scene.model_dump(by_alias=True)}
        
        The script of the whole video is here:
        Title: {video.title}
        {video.script}    
        
        Minimum number of prompts to generate: {num_images}
        
        They will all be use in the format: 
         
        Generate the stable diffusion image prompt, it will be inserted into a string like so: f"RAW photo, Fujifilm XT, clean bright modern scene photograph, <prompt>"
        
        So you just need to worry about the descriptive part. 
        
        Remember that each prompt should be completely independent, hence include specific visual descriptive details in each prompt, no prompt should be generic.
        
        For example, even if the the scene is talking about "tracks" it could be referring to a conference. So include the context of the video in each scene - location, type of event, etc.
        
        These images will be the backdrop of narrated social media reels, so they should be interesting and cool. Do not include anything related to text or logos as SDXL mangles that.
        
        Avoid text, diagrams, signage and names of people in the prompts. The image generation model will know of "San Francisco" but not of "the city". Also, avoid the word "logo" in the prompts and do not mention company or brand names as the model will not know them and will just generate gibberish. Instead, describe the image in terms of the visuals and the scene. NO DIAGRAMS. ABSTRACT ONLY.
        
        Avoid the names of celebrities. Avoid hands, feet, body parts. Do not show visualize futuristic soldiers or superheroes unless specifically demanded by the script.
        
        Try to avoid imagining AI as robots. Just don't overdo it, be cool, this counts, it's news.
        
        Examples of great prompts:
        "futuristic tech office interior, teams of young professionals working on laptops, cityscape of san francisco and bay bridge visible through large windows"
        "a bustling scene of innovators and entrepreneurs gathered in a modern, well-lit co-working space, with the iconic san francisco skyline visible through large windows"
        "iconic views of the bay bridge in San Francisco"
        "teams of young professionals deeply engaged in collaborative discussions, with laptops and whiteboards surrounding them"
        "close-up shots of diverse hackathon participants enthusiastically discussing and demonstrating their ai projects"
                
        Please return the prompts as a list of strings, one per new line. Do not include anything in your response that is not a prompt.
    """

    # Create the message for the Anthropic API
    message = client.messages.create(
        model="claude-3-opus-20240229",
        system="You are an image prompt creator for an AI video editor. You excel at answering with just prompts for image generation, one per newline",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    # Extract the profile picture detection result from the API response
    message_text = message.content[0].text.strip().lower()

    return extract_and_fill_prompts(message_text, num_images, scene.narration)
