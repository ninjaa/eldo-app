import datetime
from constants import UPLOAD_DIRECTORY
from models.scene import Scene
import io
from lib.logger import setup_logger
from octoai.clients.video_gen import Engine as VideoEngine, VideoGenerator
from PIL import Image
import base64
import os
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger(__name__)


def image_to_base64(image):
    """
    Converts an image to base64 encoded string.

    :param image: PIL Image object.
    :return: Base64 encoded string of the image.
    """
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()


async def generate_video_from_image(scene: Scene, asset_path: str):
    """
    Generates a video from an image using the OctoAI SDK.

    :param asset_path: Path to the image file.
    :param video_id: ID of the video for directory naming.
    :param index: Index of the scene for filename uniqueness.
    :param scene_videos: List to append the generated video path to.
    """
    if asset_path.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        # Instantiate the OctoAI SDK video generator
        video_gen = VideoGenerator(token=os.getenv("OCTOAI_API_TOKEN"))

        # Generate video from image using OctoAI SDK
        image = Image.open(asset_path)
        video_gen_response = video_gen.generate(
            engine=VideoEngine.SVD,
            image=image_to_base64(image),
            steps=25,
            cfg_scale=3,
            fps=6,
            motion_scale=0.2,
            noise_aug_strength=0.02,
            num_videos=1,
        )
        # Save the generated video to disk
        output_dir = f"{UPLOAD_DIRECTORY}/{scene.request_id}/{scene.aspect_ratio}/scene_videos"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"{scene.id}_img2vid_{timestamp}.mp4"
        video_path = os.path.join(output_dir, video_filename)
        with open(video_path, 'wb') as wfile:
            wfile.write(video_gen_response.videos[0].to_bytes())
        return video_path
