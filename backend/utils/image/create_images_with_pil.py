import numpy as np
from PIL import Image, ImageDraw


def create_solid_color_image(color, size, file_path):
    """
    Creates a solid color image.

    Args:
    - color: A tuple of three (RGB) or four (RGBA) integers.
    - size: A tuple of two integers, for the width and height.
    - file_path: Path to save the generated image file.
    """
    # Create an image with the specified color and size
    img = Image.new('RGB', size, color=color)
    # Save the image file
    img.save(file_path)
    return file_path


# # Usage example
# # Specify the path where you want to save the image
# solid_color_file_path = '/path/to/solid-color.png'
# color = (255, 0, 0)  # Example color (red)
# size = (1080, 1920)  # Example size for a 9:16 aspect ratio

# create_solid_color_image(color, size, solid_color_file_path)


def create_gradient_background_image(size, top_color, bottom_color, file_path):
    """
    Creates a vertical gradient background image.

    Args:
    - size: A tuple of two integers, for the width and height.
    - top_color: A tuple of three (RGB) integers for the top gradient color.
    - bottom_color: A tuple of three (RGB) integers for the bottom gradient color.
    - file_path: Path to save the generated image file.
    """
    # Create a new image with a white background
    base = Image.new('RGB', size, color=top_color)
    top = Image.new('RGB', size, color=top_color)
    bottom = Image.new('RGB', size, color=bottom_color)

    mask = Image.new('L', size)
    mask_data = []
    for y in range(size[1]):
        mask_data.extend([int(255 * (y / size[1]))] * size[0])
    mask.putdata(mask_data)

    base.paste(bottom, (0, 0), mask)
    base.paste(top, (0, 0), mask)

    draw = ImageDraw.Draw(base)

    # Optionally add more elements to the base image here

    # Save the image file
    base.save(file_path)
    return file_path


# # Usage example
# gradient_background_file_path = '/path/to/gradient-background.png'  # Specify the path
# size = (1080, 1920)  # Example size for a 9:16 aspect ratio
# top_color = (255, 225, 200)  # Light color for top (example: light pinkish tone)
# bottom_color = (200, 100, 100)  # Darker color for bottom (example: darker pinkish tone)

# create_gradient_background_image(size, top_color, bottom_color, gradient_background_file_path)


def create_circular_mask(image_path, output_path):
    # Open the original image
    im = Image.open(image_path).convert("RGBA")

    # Determine the size for a square (the larger dimension of the image)
    size = max(im.size)

    # Create a new square image
    new_im = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Paste the original image onto the square canvas, centered
    left = (size - im.size[0]) // 2
    top = (size - im.size[1]) // 2
    new_im.paste(im, (left, top))

    # Create an alpha layer with a circular mask
    alpha = Image.new('L', new_im.size, 0)
    draw = ImageDraw.Draw(alpha)
    draw.ellipse([(0, 0), (size, size)], fill=255)

    # Apply the circular mask
    new_im.putalpha(alpha)

    # Save the result with a transparent background
    new_im.save(output_path, 'PNG')
