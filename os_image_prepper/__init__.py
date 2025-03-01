import os

from . import settings
from .extracting import extract_img
from .os_image import OSImage


os.mkdir(settings.FINAL_IMAGE_DIR)


def run():
    extract_img()
    custom_image = OSImage(settings.FINAL_IMAGE_PATH)
    custom_image.customize_end_to_end(settings)


__all__ = [
    'run'
]
