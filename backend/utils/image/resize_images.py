from PIL import Image
import shutil

def convert_image_to_aspect_ratio(input_path, output_path, aspect_ratio_width, aspect_ratio_height, crop_type="contain", background_color=(0, 0, 0)):
    # Load the image
    image = Image.open(input_path)

    # Get the current image dimensions
    image_width, image_height = image.size

    # Calculate the current aspect ratio
    current_aspect_ratio = image_width / image_height

    # Check if the image is already in the desired aspect ratio
    if current_aspect_ratio == aspect_ratio_width / aspect_ratio_height:
        print("The image is already in the desired aspect ratio.")
        shutil.copy(input_path, output_path)
        print(
            f"Image copied from {input_path} to {output_path} without modification.")
        return

    # Calculate the new dimensions based on the desired aspect ratio
    desired_aspect_ratio = aspect_ratio_width / aspect_ratio_height
    if crop_type == "center":
        if current_aspect_ratio > desired_aspect_ratio:
            new_width = int(image_height * desired_aspect_ratio)
            new_height = image_height
        else:
            new_width = image_width
            new_height = int(image_width / desired_aspect_ratio)

        # Crop the image to the new dimensions
        left = (image_width - new_width) // 2
        top = (image_height - new_height) // 2
        right = left + new_width
        bottom = top + new_height
        final_image = image.crop((left, top, right, bottom))
    else:
        if current_aspect_ratio > desired_aspect_ratio:
            new_height = int(image_width / desired_aspect_ratio)
            new_width = image_width
        else:
            new_width = int(image_height * desired_aspect_ratio)
            new_height = image_height

        # Create a new blank image with the desired dimensions and color
        final_image = Image.new(
            "RGB", (new_width, new_height), background_color)

        # Calculate the position to center the image on the background
        x_position = (new_width - image_width) // 2
        y_position = (new_height - image_height) // 2

        # Paste the original image onto the new image
        final_image.paste(image, (x_position, y_position))

    # Save the final image
    final_image.save(output_path)
