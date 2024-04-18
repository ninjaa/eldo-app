
UPLOAD_DIRECTORY = "media"

# Define aspect ratio settings
ASPECT_RATIO_SETTINGS = {
    "9x16": {
        "ASPECT_RATIO": (9, 16),
        "SCREEN_SIZE": (1080, 1920),
        # "SCREEN_SIZE": (360, 640),
        "top_spacing": 0.3,
        "bottom_spacing": 0.8,
        "logo_relative_size": 0.15,
        "logo_bottom_spacing": 0.7,
    },
    "16x9": {
        "ASPECT_RATIO": (16, 9),
        "SCREEN_SIZE": (1920, 1080),
        "top_spacing": 0.2,
        "bottom_spacing": 0.75,
        "logo_relative_size": 0.1,
        "logo_bottom_spacing": 0.65,
    },
    "1x1": {
        "ASPECT_RATIO": (1, 1),
        "SCREEN_SIZE": (1080, 1080),
        "top_spacing": 0.25,
        "bottom_spacing": 0.75,
        "logo_relative_size": 0.2,
        "logo_bottom_spacing": 0.7,
    }
}
