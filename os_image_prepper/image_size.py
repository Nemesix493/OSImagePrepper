from logging import getLogger
import subprocess


logger = getLogger("GlobalLogger")


def extend_image(image_path, size_mo):
    logger.info(f"🔄 Adding {size_mo} Mo to : {image_path}")
    try:
        subprocess.run(["dd", "if=/dev/zero", "bs=1M", f"count={size_mo}", ">>", image_path], check=True)
        logger.info(f"✅ {size_mo} Mo added to : {image_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Adding {size_mo} Mo failed due to this error :\n {e}")
        exit(1)
