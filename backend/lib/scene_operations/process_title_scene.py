from constants import ASPECT_RATIO_SETTINGS
from utils.image.create_images_with_pil import create_circular_mask
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
from PIL import Image, ImageOps
logger = setup_logger(__name__)

_client, db = get_db_connection()


def wrap_text(text, font, font_size, max_width):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if TextClip(current_line + " " + word, font=font, fontsize=font_size).size[0] <= max_width:
            current_line += " " + word
        else:
            lines.append(current_line.strip())
            current_line = word
    if current_line:
        lines.append(current_line.strip())
    return "\n".join(lines)


async def process_title_scene(scene: Scene, run_suffix: str = "", draw_bounding_box=False, gradient_color=(173, 216, 230), gradient_color2=(0, 0, 139)):
    ratio_settings = ASPECT_RATIO_SETTINGS.get(
        scene.aspect_ratio, ASPECT_RATIO_SETTINGS["9x16"])

    SCREEN_SIZE = ratio_settings["SCREEN_SIZE"]

    generated_images_directory_path = os.path.join(
        UPLOAD_DIRECTORY, scene.request_id, scene.aspect_ratio, "scene_images")
    os.makedirs(generated_images_directory_path, exist_ok=True)
    gradient_bg_path = f"{generated_images_directory_path}/{scene.id}_gradient.png"
    create_gradient_background_image(
        SCREEN_SIZE, gradient_color, gradient_color2, gradient_bg_path
    )
    max_text_width = SCREEN_SIZE[0] * 0.8  # Allow 80% of screen width for text
    font_size = int(SCREEN_SIZE[1] / 25)
    line_spacing = font_size / 3

    # Define the desired spacing from the top and bottom edges
    top_spacing = int(SCREEN_SIZE[1] * ratio_settings["top_spacing"])
    bottom_spacing = int(SCREEN_SIZE[1] * ratio_settings["bottom_spacing"])

    # Assume we have a function that retrieves the logo upload details
    logo_upload = get_logo_upload(scene.request_id)
    logo_relative_size = ratio_settings["logo_relative_size"]

    # After resizing the logo, calculate its height
    logo_height = SCREEN_SIZE[0] * logo_relative_size
    # Now, adjust logo_bottom_spacing to place the center of the logo at 70% of the screen height
    logo_bottom_spacing = int(
        SCREEN_SIZE[1] * ratio_settings["logo_bottom_spacing"])
    logger.info(f"Logo height: {logo_height}")
    logger.info(f"Logo bottom spacing: {logo_bottom_spacing}")

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
        font = "Helvetica-Bold"
        font_size = 200  # Adjust the font size as needed
        text_color = (255, 255, 255)  # White color, adjust as needed

        # Create a text clip for the letter
        letter_clip = TextClip(letter, fontsize=font_size,
                               color=text_color, font=font)
        letter_clip = letter_clip.set_duration(scene.duration)

        # Resize the letter clip to fit the screen appropriately
        letter_clip = letter_clip.resize(
            height=SCREEN_SIZE[1] * logo_relative_size)

        # Set the position of the letter clip
        letter_clip = letter_clip.set_position('center', logo_bottom_spacing)

        # Use the letter clip in place of the logo
        logo_clip = letter_clip
    else:
        logo_with_circular_mask_path = os.path.join(
            generated_images_directory_path, "logo_with_circular_mask.png")
        create_circular_mask(logo_upload.file_path,
                             logo_with_circular_mask_path)

        if draw_bounding_box:
            # Open the image using PIL
            logo_image = Image.open(logo_with_circular_mask_path)
            # Define border color and thickness
            border_color = 'black'  # Change this to your desired border color
            border_thickness = 10  # Change this to your desired border thickness
            # Add a border to the image
            logo_image_with_border = ImageOps.expand(
                logo_image, border=border_thickness, fill=border_color)
            # Save the image back
            logo_image_with_border.save(logo_with_circular_mask_path)

        logo_clip = ImageClip(
            logo_with_circular_mask_path).set_duration(scene.duration)
        # Resize logo to 60% of the screen width
        logo_clip = logo_clip.resize(
            width=(SCREEN_SIZE[0] * logo_relative_size))
        logo_height = logo_clip.h
        logo_clip = logo_clip.set_position((
            'center', SCREEN_SIZE[1] * 0.7 - logo_height/2))

    # Create a text clip for the narration text
    # wrapped_narration = wrap_text(
        # scene.narration, "Lato", font_size, max_text_width)
    # logger.info(f"Narration: {wrapped_narration}")
    narration_text = TextClip(
        scene.narration,
        fontsize=font_size,
        color='white',
        size=(max_text_width, None),
        font="Helvetica-Bold",
        method="caption",
        align="center",
        interline=line_spacing
    )
    narration_text = narration_text.set_position(
        ('center', top_spacing)).set_duration(scene.duration)

    # Create a text clip for the social media handle
    social_media_text = TextClip(
        brand_link,
        fontsize=int(font_size * 0.6),
        color='white',
        size=(max_text_width, None),
        font="Helvetica"
    )
    social_media_text = social_media_text.set_position(
        ('center', bottom_spacing)).set_duration(scene.duration)

    # Composite all the clips together
    composite_clip = CompositeVideoClip(
        [background_clip, logo_clip, narration_text, social_media_text])
    composite_clip = composite_clip.set_duration(scene.duration)

    # Load the scene narration audio
    narrations_directory_path = os.path.join(
        UPLOAD_DIRECTORY, scene.request_id, scene.aspect_ratio, "scene_narrations")
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
        return await process_title_scene(
            scene,
            run_suffix=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            draw_bounding_box=False
        )
    else:
        logger.error(f"Scene with id {scene_id} not found")
        return None
