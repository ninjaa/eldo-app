from constants import UPLOAD_DIRECTORY
from models.scene import Scene
from moviepy.editor import AudioFileClip, ImageClip, TextClip, CompositeVideoClip
# Make sure to define these functions.
from utils.helpers import get_logo_upload, get_brand_link
from utils.image.create_images_with_pil import create_gradient_background_image
from lib.database import get_db_connection
from lib.logger import setup_logger
import os
from datetime import datetime

logger = setup_logger(__name__)

_client, db = get_db_connection()

# Define the aspect ratio dimensions
ASPECT_RATIO = (9, 16)
SCREEN_SIZE = (1080, 1920)  # Example resolution based on 9:16 aspect ratio


async def process_title_scene(scene: Scene, run_suffix: str = ""):
    generated_images_directory_path = os.path.join(
        UPLOAD_DIRECTORY, scene.request_id, scene.aspect_ratio, "generated_images")
    os.makedirs(generated_images_directory_path, exist_ok=True)
    gradient_bg_path = f"{generated_images_directory_path}/{scene.id}_gradient.png"
    create_gradient_background_image(
        SCREEN_SIZE, (173, 216, 230), (0, 0, 139), gradient_bg_path
    )
    max_text_width = SCREEN_SIZE[0] * 0.8  # Allow 80% of screen width for text
    font_size = int(SCREEN_SIZE[1] / 25)
    # Define the desired spacing from the top and bottom edges
    top_spacing = int(SCREEN_SIZE[1] * 0.1)  # 10% of the screen height
    bottom_spacing = int(SCREEN_SIZE[1] * 0.05)  # 5% of the screen height

    # Assume we have a function that retrieves the logo upload details
    logo_upload = get_logo_upload(scene.request_id)
    # And another that retrieves the brand link
    brand_link = get_brand_link(scene.request_id)

    # Create a background clip of solid color
    background_clip = ImageClip(gradient_bg_path, duration=scene.duration)
    background_clip = background_clip.set_position(
        'center').set_duration(scene.duration)

    # Load the logo and resize it to fit the screen appropriately
    if logo_upload is None:
        # Generate a capital letter in a cool font
        letter = "M"  # @TODO Replace with the desired letter
        # Replace with the path to the cool font file
        font = "Lato-Black"
        font_size = 200  # Adjust the font size as needed
        text_color = (255, 255, 255)  # White color, adjust as needed

        # Create a text clip for the letter
        letter_clip = TextClip(letter, fontsize=font_size,
                               color=text_color, font=font)
        letter_clip = letter_clip.set_duration(scene.duration)

        # Resize the letter clip to fit the screen appropriately
        letter_clip = letter_clip.resize(height=SCREEN_SIZE[1] * 0.6)

        # Set the position of the letter clip
        letter_clip = letter_clip.set_pos('center')

        # Use the letter clip in place of the logo
        logo_clip = letter_clip
    else:
        logo_clip = ImageClip(
            logo_upload.file_path).set_duration(scene.duration)
        # Resize logo to 60% of the screen width
        logo_clip = logo_clip.resize(width=(SCREEN_SIZE[0] * 0.6))
        logo_clip = logo_clip.set_pos('center')

    # Create a text clip for the narration text
    narration_text = TextClip(
        scene.narration,
        fontsize=font_size,
        color='white',
        size=(max_text_width, None),
        font="Verdana",
        method="caption",
        align="center"
    )
    narration_text = narration_text.set_position(
        ('center', top_spacing)).set_duration(scene.duration)

    # Create a text clip for the social media handle
    social_media_text = TextClip(
        brand_link,
        fontsize=int(font_size * 0.7),
        color='white',
        size=(max_text_width, None),
        font="Verdana"
    )
    social_media_text = social_media_text.set_position(
        ('center', bottom_spacing)).set_duration(scene.duration)

    # Composite all the clips together
    composite_clip = CompositeVideoClip(
        [background_clip, logo_clip, narration_text, social_media_text])
    composite_clip = composite_clip.set_duration(scene.duration)

    # Load the scene narration audio
    narrations_directory_path = os.path.join(
        UPLOAD_DIRECTORY, scene.request_id, "scene_narrations", scene.aspect_ratio)
    narration_audio_path = os.path.join(
        narrations_directory_path, scene.narration_audio_filename)
    narration_audio = AudioFileClip(narration_audio_path)
    # Set the audio of the composite clip to be the narration audio
    composite_clip = composite_clip.set_audio(narration_audio)

    # Set the final size to match the aspect ratio
    composite_clip = composite_clip.resize(SCREEN_SIZE)

    # You can write to a file or return the clip to be used in further processing
    # Save the scene as a video file
    output_directory = os.path.join(
        UPLOAD_DIRECTORY, scene.request_id, scene.aspect_ratio, "scene_videos")
    os.makedirs(output_directory, exist_ok=True)
    output_filename = f"{scene.id}_title_scene{'_' + run_suffix if run_suffix else ''}.mp4"
    output_path = os.path.join(output_directory, output_filename)
    composite_clip.write_videofile(output_path, fps=24)

    return output_path  # Optionally return the filename of the generated video clip

# Later on, you can call this function with an appropriate event loop
# For example:
# asyncio.run(process_title_scene(scene))


async def process_title_scene_by_id(scene_id):
    scene_result = db.scenes.find_one({"_id": scene_id})
    if scene_result:
        scene = Scene(**scene_result)
        return await process_title_scene(scene, run_suffix=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    else:
        logger.error(f"Scene with id {scene_id} not found")
        return None
