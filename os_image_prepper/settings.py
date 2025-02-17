from datetime import datetime
import logging
import os
from pathlib import Path

# Define path

WORK_DIR = Path("/workspace/")

DATA_DIR = WORK_DIR / "data"

datetime_now = datetime.now()

# Init logger

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

logger = logging.getLogger("GlobalLogger")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler(DATA_DIR / f"{datetime_now.strftime('%m-%d-%Y-%H-%M-%S')}.log", mode="a")
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.setLevel(
    LOG_LEVELS.get(
        str(
            os.getenv(
                'LOG_LEVEL',
                'DEBUG'
            )
        ).upper(),
        logging.DEBUG
    )
)

# Load params from ENV

BASE_IMAGE_PATH = DATA_DIR / os.getenv('BASE_IMAGE_PATH', 'base_img.img')

FINAL_IMAGE_NAME = os.getenv('FINAL_IMAGE_NAME', 'new-image')

FINAL_IMAGE_DIR = DATA_DIR / f"{datetime_now.strftime('%Y-%m-%d')}{FINAL_IMAGE_NAME}"

FINAL_IMAGE_PATH = FINAL_IMAGE_DIR / f"{datetime_now.strftime('%Y-%m-%d')}{FINAL_IMAGE_NAME}.img"

KEEP_BASE_IMAGE = bool(os.getenv('KEEP_BASE_IMAGE', 1))
