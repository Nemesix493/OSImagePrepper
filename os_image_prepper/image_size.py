from logging import getLogger
from pathlib import Path
import subprocess
import time


logger = getLogger("GlobalLogger")


class OSImage:
    def __init__(self, image_path: Path):
        if not image_path.exists():
            value_error = ValueError(f"Image \"{image_path}\" doesn't exist !")
            logger.error(f"❌ Can't manage \"{image_path}\" image due to this error :\n {value_error}")
            raise value_error
        self._image_path = image_path
        self._is_mounted = False
        self._is_partitions_mapped = False
        self._loop_dev = None
        self._boot_partition = None
        self._root_partition = None

    # Define properties

    @property
    def path(self):
        return self._image_path

    @property
    def loop_dev(self):
        return self._loop_dev

    @property
    def boot_partition(self):
        return self._boot_partition

    @property
    def root_partition(self):
        return self._root_partition

    # Define mounting and mapping (core methods)

    def mount(self):
        if not self._is_mounted:
            logger.info(f"🔄 Mounting : {self.path}")
            try:
                losetup = subprocess.run(["losetup", "-Pf", "--show", self.path], check=True, text=True).stdout
                logger.debug(f"losetup -Pf --show {self.path} -> {losetup}")
                time.sleep(2)
                self._is_mounted = True
                self._loop_dev = Path(losetup)
                logger.info("✅ Image successfully mounted !")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Mounting {self.path} failed due to this error :\n {e}")
                exit(1)
        return self.loop_dev

    def unmount(self):
        if self._is_mounted:
            self.unmap_partitions()
            logger.info(f"🔄 Unounting : {self.path}")
            try:
                losetup = subprocess.run(["losetup", "-d", self.path], check=True, text=True).stdout
                logger.debug(f"losetup -d {self.path} -> {losetup}")
                time.sleep(2)
                self._is_mounted = False
                self._loop_dev = None
                logger.info("✅ Image successfully unmounted !")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Unmounting {self.path} failed due to this error :\n {e}")
                exit(1)

    def map_partitions(self):
        if not self._is_partitions_mapped:
            self.mount()
            logger.info(f"🔄 Mapping partitions from {self.path}")
            try:
                kpartx = subprocess.run(["kpartx", "-av", self.loop_dev], check=True, text=True).stdout
                logger.debug(f"kpartx -av {self.loop_dev} -> {kpartx}")
                time.sleep(2)
                self._is_partitions_mapped = True
                self._boot_partition = Path(f"/dev/mapper/{self.loop_dev.name}p1")
                self._root_partition = Path(f"/dev/mapper/{self.loop_dev.name}p2")
                logger.info("✅ Partitions successfully mapped !")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Mapping partitions from {self.path} failed due to this error :\n {e}")
                exit(1)

    def unmap_partitions(self):
        if self._is_partitions_mapped:
            logger.info(f"🔄 Unmapping partitions from {self.path}")
            try:
                kpartx = subprocess.run(["kpartx", "-d", self.loop_dev], check=True, text=True).stdout
                logger.debug(f"kpartx -d {self.loop_dev} -> {kpartx}")
                time.sleep(2)
                self._is_partitions_mapped = False
                self._boot_partition = None
                self._root_partition = None
                logger.info("✅ Partitions successfully unmapped !")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Unmapping partitions from {self.path} failed due to this error :\n {e}")
                exit(1)

    # Define public methods (main functionality)

    def extend_image(self, size_mo: int):
        self.unmount()
        logger.info(f"🔄 Adding {size_mo} Mo to : {self.path}")
        try:
            dd = subprocess.run(
                ["dd", "if=/dev/zero", "bs=1M", f"count={size_mo}", ">>", self.path],
                check=True,
                text=True
            ).stdout
            logger.debug(f"dd if=/dev/zero bs=1M count={size_mo} >> self.path -> {dd}")
            logger.info(f"✅ {size_mo} Mo successfully added to : {self.path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Adding {size_mo} Mo failed due to this error :\n {e}")
            exit(1)

    def extend_root_partition(self):
        self.mount()
        self.unmap_partitions()
        logger.info(f"🔄 Extending root partition : {self.path}")
        try:
            parted = subprocess.run(
                ["parted", "--script", self.loop_dev, "resizepart", "2", "100%"],
                check=True,
                text=True
            ).stdout
            logger.debug(f"parted --script {self.loop_dev} resizepart 2 100% -> {parted}")
            logger.info("✅ root partition successfully extended")
        except subprocess.CalledProcessError as e:
            self.unmount()
            logger.error(f"❌ root partition extention failed due to this error :\n {e}")
            exit(1)

    def extend_root_fs(self):
        self.map_partitions()
        logger.info(f"🔄 Extending root filesystem from {self.path}")
        try:
            e2fsck = subprocess.run(["e2fsck", "-f", self.root_partition], check=True, text=True).stdout
            logger.debug(f"e2fsck -f {self.root_partition} -> {e2fsck}")
            resize2fs = subprocess.run(["resize2fs", self.root_partition], check=True, text=True).stdout
            logger.debug(f"resize2fs {self.root_partition} -> {resize2fs}")
            logger.info("✅ root filesystem successfully extended")
        except subprocess.CalledProcessError as e:
            self.unmount()
            logger.error(f"❌ root filesystem extention failed due to this error :\n {e}")
            exit(1)

    def add_root_space(self, size_mo: int):
        self.extend_image(size_mo)
        self.extend_root_partition()
        self.extend_root_fs()
