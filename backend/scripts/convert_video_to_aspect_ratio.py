import argparse
import sys
import os

# Add the project's root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.video.resize_videos import convert_video_to_aspect_ratio


# example usage python scripts/convert_video_to_aspect_ratio.py ./media/multion-example/testimonial.mp4 ./media/testimonial_9_16_contain.mp4 9 16 --crop_type contain --background_color 0 0 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a video to a specified aspect ratio.")
    parser.add_argument("input_path", help="Path to the input video file.")
    parser.add_argument(
        "output_path", help="Path to save the output video file.")
    parser.add_argument("aspect_ratio_width", type=int,
                        help="Width of the desired aspect ratio.")
    parser.add_argument("aspect_ratio_height", type=int,
                        help="Height of the desired aspect ratio.")
    parser.add_argument("--crop_type", choices=["contain", "center"],
                        default="contain", help="Crop type: 'contain' (default) or 'center'.")
    parser.add_argument("--background_color", nargs=3, type=int,
                        default=[0, 0, 0], help="Background color in RGB format (default: black).")
    args = parser.parse_args()

    convert_video_to_aspect_ratio(args.input_path, args.output_path, args.aspect_ratio_width,
                                  args.aspect_ratio_height, args.crop_type, tuple(args.background_color))
