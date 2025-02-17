import os

from . import settings
from .extracting import extract_img


os.mkdir(settings.FINAL_IMAGE_DIR)


def run():
    extract_img()


__all__ = [
    'run'
]
