from logging import getLogger
from os import mkdir
from pathlib import Path
import subprocess
import time


logger = getLogger("GlobalLogger")


class OSImage:

    BIND_SYSTEM_DIRS = [
        "dev",
        "sys",
        "proc",
        "dev/pts"
    ]

    def __init__(self, image_path: Path):
        if not image_path.exists():
            value_error = ValueError(f"Image \"{image_path}\" doesn't exist !")
            logger.error(f"❌ Can't manage \"{image_path}\" image due to this error :\n {value_error}")
            raise value_error
        self._image_path = image_path
        self._is_mounted = False
        self._is_partitions_mapped = False
        self._is_system_dirs_bound = False
        self._is_partitions_mounted = False
        self._loop_dev = None
        self._boot_partition = None
        self._root_partition = None
        self._root_mount_dir = Path("/mnt/image_bind")
        self._boot_mount_dir = self._root_mount_dir / "boot"

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

    def mount_image_partitions(self):
        if not self._is_partitions_mounted:
            self.map_partitions()
            if not self._root_mount_dir.exists():
                mkdir(self._root_mount_dir)
            if not self._boot_mount_dir.exists():
                mkdir(self._boot_mount_dir)
            logger.info(f"🔄 Mounting image partitions from {self.path} into {self._root_mount_dir}")
            try:
                # Mounting root partition
                mount_root = subprocess.run(
                    ["mount", self.root_partition, self._root_mount_dir],
                    check=True,
                    text=True
                ).stdout
                logger.debug(f"mount {self.root_partition} {self._root_mount_dir} -> {mount_root}")
                # Mounting boot partition
                mount_boot = subprocess.run(
                    ["mount", self.boot_partition, self._boot_mount_dir],
                    check=True,
                    text=True
                ).stdout
                logger.debug(f"mount {self.boot_partition} {self._boot_mount_dir} -> {mount_boot}")
                logger.info("✅ Image partitions successfully mounted !")
                self._is_partitions_mounted = True
            except subprocess.CalledProcessError as e:
                self.unmount()
                logger.error(f"❌ Mounting image partitions from {self.path} failed due to this error :\n {e}")
                exit(1)

    def unmount_image_partitions(self):
        if self._is_partitions_mounted:
            self.unbind_system_dirs()
            logger.info(f"🔄 Unmounting image partitions {self._root_mount_dir}")
            try:
                # Unmounting boot partition
                umount_boot = subprocess.run(["umount", self._boot_mount_dir], check=True, text=True).stdout
                logger.debug(f"umount {self._boot_mount_dir} -> {umount_boot}")
                # Unmounting root partition
                umount_root = subprocess.run(["umount", self._root_mount_dir], check=True, text=True).stdout
                logger.debug(f"umount {self._root_mount_dir} -> {umount_root}")
                self._is_partitions_mounted = False
                logger.info("✅ Image partitions successfully unmounted !")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Unmounting image partitions from {self.path} failed due to this error :\n {e}")
                exit(1)

    def bind_system_dirs(self):
        if not self._is_system_dirs_bound:
            self.mount_image_partitions()
            logger.info(f"🔄 Binding system directories for {self.path}")
            try:
                # Binding system dirs
                for system_dir in self.BIND_SYSTEM_DIRS:
                    system_dir_path = Path("/") / system_dir
                    system_dir_bind_path = self._root_mount_dir / system_dir
                    mount_bind = subprocess.run(
                        ["mount", "--bind", system_dir_path, system_dir_bind_path],
                        check=True,
                        text=True
                    ).stdout
                    logger.debug(f"mount --bind {system_dir_path} {system_dir_bind_path} -> {mount_bind}")
                self._is_system_dirs_bound = True
                logger.info("✅ System directories successfully bound !")
            except subprocess.CalledProcessError as e:
                self.unmount()
                logger.error(f"❌ Binding system directories for {self.path} failed due to this error :\n {e}")
                exit(1)

    def unbind_system_dirs(self):
        if self._is_system_dirs_bound:
            logger.info(f"🔄 Unbinding system directories for {self.path}")
            try:
                # Unbinding system dirs
                for system_dir in reversed(self.BIND_SYSTEM_DIRS):
                    system_dir_bind_path = self._root_mount_dir / system_dir
                    umount_bind = subprocess.run(
                        ["umount", system_dir_bind_path],
                        check=True,
                        text=True
                    ).stdout
                    logger.debug(f"umount {system_dir_bind_path} -> {umount_bind}")
                self._is_system_dirs_bound = False
                logger.info("✅ System directories successfully unbound !")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Unbinding system directories for {self.path} failed due to this error :\n {e}")
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
