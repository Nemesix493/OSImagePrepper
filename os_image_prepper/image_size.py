from logging import getLogger
from pathlib import Path
import subprocess
import time


logger = getLogger("GlobalLogger")


def extend_image(image_path, size_mo):
    logger.info(f"🔄 Adding {size_mo} Mo to : {image_path}")
    try:
        subprocess.run(["dd", "if=/dev/zero", "bs=1M", f"count={size_mo}", ">>", image_path], check=True)
        logger.info(f"✅ {size_mo} Mo added to : {image_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Adding {size_mo} Mo failed due to this error :\n {e}")
        exit(1)


def extend_root_partition(image_path):
    logger.info(f"🔄 Extending root partition  : {image_path}")
    try:
        loop_dev = subprocess.run(["losetup", "-Pf", "--show", image_path], check=True, text=True)
        logger.debug(f"losetup -Pf --show $IMAGE_PATH -> {loop_dev.stdout}")
        time.sleep(2)
        subprocess.run(["parted", "--script", loop_dev.stdout, "resizepart", "2", "100%"])
        subprocess.run(["losetup", "-d", loop_dev.stdout])
        logger.info("✅ root partition extended")
    except subprocess.CalledProcessError as e:
        subprocess.run(["losetup", "-d", loop_dev.stdout])
        logger.error(f"❌ root partition extention failed due to this error :\n {e}")
        exit(1)


def extend_root_fs(image_path):
    try:
        loop_dev = subprocess.run(["losetup", "-Pf", "--show", image_path], check=True, text=True)
        logger.debug(f"losetup -Pf --show $IMAGE_PATH -> {loop_dev.stdout}")
        subprocess.run(["kpartx", "-av", loop_dev.stdout], check=True)
        time.sleep(2)
        root_partition = Path(f"/dev/mapper/{Path(loop_dev.stdout).name}p2")
        logger.debug(f"root_partition -> {root_partition}")
        subprocess.run(["e2fsck", "-f", root_partition], check=True, text=True).stdout
        subprocess.run(["resize2fs", root_partition], check=True, text=True).stdout
        subprocess.run(["kpartx", "-d", loop_dev.stdout], check=True)
        subprocess.run(["losetup", "-d", loop_dev.stdout], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ root partition extention failed due to this error :\n {e}")
        exit(1)
