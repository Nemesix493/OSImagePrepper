import subprocess
from logging import getLogger

from .settings import (
    BASE_IMAGE_PATH,
    FINAL_IMAGE_PATH,
    KEEP_BASE_IMAGE
)


logger = getLogger("GlobalLogger")


def extract_img():
    methods = {
        '.img': no_need_to_extract,
        '.xz': extract_img_from_xz
    }
    method = methods.get(
        BASE_IMAGE_PATH.suffix,
        None
    )
    if method is None:
        raise ValueError(f"'{BASE_IMAGE_PATH.suffix}' file is no supported")
    method(BASE_IMAGE_PATH, FINAL_IMAGE_PATH, KEEP_BASE_IMAGE)


def no_need_to_extract(input_file, output_file, keep_base_file):
    if keep_base_file:
        try:
            logger.info(f"🔄 Copying {input_file} into {output_file}")
            subprocess.run(["cp", input_file, output_file], check=True)
            logger.info(f"✅ {output_file} is copied !")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Copy failed due to this error :\n {e}")
            exit(1)
    else:
        try:
            logger.info(f"🔄 Moving {input_file} into {output_file}")
            subprocess.run(["cp", input_file, output_file], check=True)
            logger.info(f"✅ {output_file} is moved !")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Move failed due to this error :\n {e}")
            exit(1)


def extract_img_from_xz(input_file, output_file, keep_base_file):
    logger.info(f"🔄 Extracting {input_file} into {input_file}")
    xz_args = "-dkc" if keep_base_file else "-dc"
    try:
        subprocess.run(["xz", xz_args, input_file, ">", output_file], check=True)
        logger.info(f"✅ {output_file} is extracted !")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Extraction failed due to this error :\n {e}")
        exit(1)
