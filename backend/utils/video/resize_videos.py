from moviepy.editor import ColorClip, CompositeVideoClip, VideoFileClip
from utils.video.video_helpers import get_video_size

import shutil
# default codec is 'libx264'
# default bitrate is 2000


def convert_video_to_aspect_ratio(input_path, output_path, aspect_ratio_width, aspect_ratio_height, crop_type="contain", background_color=(0, 0, 0)):

    # Get the video size using the get_video_size function
    video_width, video_height = get_video_size(input_path)

    # Load the video clip
    video = VideoFileClip(input_path)
    
    # Manually set the video width and height by resizing
    # Replace (new_width, new_height) with your desired dimensions
    video = video.resize(newsize=(video_width, video_height))


    # Calculate the current aspect ratio
    current_aspect_ratio = video_width / video_height
    print(f"video width is {video_width}")
    print(f"video height is {video_height}")
    print(f"current aspect ratio is {current_aspect_ratio}")
    print(
        f"desired aspect ratio is {aspect_ratio_width} / {aspect_ratio_height}")
    # Check if the video is already in the desired aspect ratio
    if current_aspect_ratio == aspect_ratio_width / aspect_ratio_height:
        print("The video is already in the desired aspect ratio.")
        shutil.copy(input_path, output_path)
        print(
            f"Video copied from {input_path} to {output_path} without modification.")
        return

    # Calculate the new dimensions based on the desired aspect ratio
    desired_aspect_ratio = aspect_ratio_width / aspect_ratio_height
    if crop_type == "contain":
        if current_aspect_ratio > desired_aspect_ratio:
            new_height = int(video_width / desired_aspect_ratio)
            new_width = video_width
        else:
            new_width = int(video_height * desired_aspect_ratio)
            new_height = video_height

        # Create a new background clip with the desired dimensions and color
        background_clip = ColorClip(
            size=(new_width, new_height), color=background_color)

        # Calculate the position to center the video on the background
        x_position = (new_width - video_width) // 2
        y_position = (new_height - video_height) // 2

        # Overlay the video on the background
        final_clip = CompositeVideoClip(
            [background_clip, video.set_position((x_position, y_position))])
        final_clip = final_clip.set_duration(video.duration)
    else:
        if current_aspect_ratio > desired_aspect_ratio:
            new_width = int(video_height * desired_aspect_ratio)
            new_height = video_height
        else:
            new_width = video_width
            new_height = int(video_width / desired_aspect_ratio)

        # Crop the video to the new dimensions
        x1 = (video_width - new_width) // 2
        y1 = (video_height - new_height) // 2
        x2 = x1 + new_width
        y2 = y1 + new_height
        final_clip = video.crop(x1=x1, y1=y1, x2=x2, y2=y2)

    # Write the final clip to a file
    final_clip.write_videofile(
        output_path)
