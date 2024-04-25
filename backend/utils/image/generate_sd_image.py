from PIL import Image
from octoai.clients.image_gen import Engine, ImageGenerator
import os
from dotenv import load_dotenv
from models.scene import Scene
from constants import ASPECT_RATIO_SETTINGS, UPLOAD_DIRECTORY
from lib.logger import setup_logger

logger = setup_logger(__name__)

load_dotenv()


# Instantiate the OctoAI SDK image generator
image_gen = ImageGenerator(token=os.getenv("OCTOAI_API_TOKEN"))


def generate_image(scene: Scene, prompt, index: int) -> str:
    """
    Generates an image based on the scene's narration using the OctoAI SDK.

    :return: The path to the generated image.
    """
    # Generate the stable diffusion image prompt
    logger.info(f"Generating image for scene {scene.id} with prompt {prompt}")
    prompt = f"RAW photo, Fujifilm XT, clean bright modern scene photograph, inspired by the movie Drive's aesthetics but more colorful and cheerful as well, sci-fi, futuristic, {prompt}"
    ASPECT_RATIO = ASPECT_RATIO_SETTINGS[scene.aspect_ratio]["ASPECT_RATIO"]
    SCREEN_SIZE = ASPECT_RATIO_SETTINGS[scene.aspect_ratio]["SCREEN_SIZE"]
    if ASPECT_RATIO == "16:9":
        width = 1365
        height = 768
    elif ASPECT_RATIO == "1:1":
        width = 1024
        height = 1024
    else:
        width = 768
        height = 1344

    # Generate the image using the OctoAI SDK
    image_gen_response = image_gen.generate(
        engine=Engine.SDXL,
        prompt=prompt,
        negative_prompt="Blurry photo, distortion, low-res, poor quality, watermark, text, Ryan Gosling",
        width=width,
        height=height,
        num_images=1,
        sampler="DPM_PLUS_PLUS_2M_KARRAS",
        steps=30,
        cfg_scale=12,
        use_refiner=True,
        high_noise_frac=0.8,
    )

    # Save the generated image to disk
    output_dir = f"{UPLOAD_DIRECTORY}/{scene.request_id}/{scene.aspect_ratio}/scene_images"
    os.makedirs(output_dir, exist_ok=True)
    image_filename = f"{scene.id}_generated_image_{index}.png"
    image_path = os.path.join(output_dir, image_filename)
    image = image_gen_response.images[0].to_pil()
    image.save(image_path)

    original_image = Image.open(image_path)
    resized_image = original_image.resize(SCREEN_SIZE)
    resized_image.save(image_path)  # Overwrite the original image

    return image_path
