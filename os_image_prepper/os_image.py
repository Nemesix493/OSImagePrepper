from logging import getLogger
from os import mkdir
from pathlib import Path
import subprocess
import time
import yaml


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
        self._mount_packages_dir = self._root_mount_dir / "packages"
        self._image_packages_dir = Path("/packages")

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
                losetup = subprocess.run(["losetup", "-d", self.loop_dev], check=True, text=True).stdout
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
                self.unmount()
                exit(1)

    def unmap_partitions(self):
        if self._is_partitions_mapped:
            self.unmount_image_partitions()
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

    def mount_device(self, device_path: Path, into_path: Path, catch_exception: bool = True):
        logger.info(f"🔄 Mounting {device_path} into {into_path}")
        try:
            mount_bind = subprocess.run(
                ["mount", device_path, into_path],
                check=True,
                text=True
            ).stdout
            logger.debug(f"mount {device_path} {into_path} -> {mount_bind}")
            logger.info(f"✅ {device_path} successfully mounted into {into_path} !")
        except subprocess.CalledProcessError as e:
            if catch_exception:
                logger.error(f"❌ Mounting {device_path} into {into_path} failed due to this error :\n {e}")
                self.unmount()
                exit(1)
            else:
                logger.error(f"❌ Mounting {device_path} into {into_path} failed !")
                raise e

    def unmount_device_or_directory(self, mount_point: Path, catch_exception: bool = True):
        logger.info(f"🔄 Unmounting {mount_point}")
        try:
            umount = subprocess.run(
                ["umount", mount_point],
                check=True,
                text=True
            ).stdout
            logger.debug(f"umount {mount_point} -> {umount}")
            logger.info(f"✅ {mount_point} successfully unmounted !")
        except subprocess.CalledProcessError as e:
            if catch_exception:
                logger.error(f"❌ Unmounting {mount_point} failed due to this error :\n {e}")
                exit(1)
            else:
                logger.error(f"❌ Unmounting {mount_point} failed !")
                raise e

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
                self.mount_device(self.root_partition, self._root_mount_dir, False)
                # Mounting boot partition
                self.mount_device(self.boot_partition, self._boot_mount_dir, False)
                logger.info("✅ Image partitions successfully mounted !")
                self._is_partitions_mounted = True
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Mounting image partitions from {self.path} failed due to this error :\n {e}")
                self.unmount()
                exit(1)

    def unmount_image_partitions(self):
        if self._is_partitions_mounted:
            self.unbind_system_dirs()
            logger.info(f"🔄 Unmounting image partitions {self._root_mount_dir}")
            try:
                # Unmounting boot partition
                self.unmount_device_or_directory(self._boot_mount_dir, False)
                # Unmounting root partition
                self.unmount_device_or_directory(self._root_mount_dir, False)
                self._is_partitions_mounted = False
                logger.info("✅ Image partitions successfully unmounted !")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Unmounting image partitions from {self.path} failed due to this error :\n {e}")
                exit(1)

    def mount_bind_directory(self, from_path: Path, into_path: Path, catch_exception: bool = True):
        logger.info(f"🔄 Binding {from_path} into {into_path}")
        try:
            mount_bind = subprocess.run(
                ["mount", "--bind", from_path, into_path],
                check=True,
                text=True
            ).stdout
            logger.debug(f"mount --bind {from_path} {into_path} -> {mount_bind}")
            logger.info(f"✅ {from_path} successfully bound into {into_path} !")
        except subprocess.CalledProcessError as e:
            if catch_exception:
                logger.error(f"❌ Binding {from_path} into {into_path} failed due to this error :\n {e}")
                self.unmount()
                exit(1)
            else:
                logger.error(f"❌ Binding {from_path} into {into_path} failed !")
                raise e

    def bind_system_dirs(self):
        if not self._is_system_dirs_bound:
            self.mount_image_partitions()
            logger.info(f"🔄 Binding system directories for {self.path}")
            try:
                # Binding system dirs
                for system_dir in self.BIND_SYSTEM_DIRS:
                    system_dir_path = Path("/") / system_dir
                    system_dir_bind_path = self._root_mount_dir / system_dir
                    self.mount_bind_directory(system_dir_path, system_dir_bind_path, False)
                self._is_system_dirs_bound = True
                logger.info("✅ System directories successfully bound !")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Binding system directories for {self.path} failed due to this error :\n {e}")
                self.unmount()
                exit(1)

    def unbind_system_dirs(self):
        if self._is_system_dirs_bound:
            logger.info(f"🔄 Unbinding system directories for {self.path}")
            try:
                # Unbinding system dirs
                for system_dir in reversed(self.BIND_SYSTEM_DIRS):
                    system_dir_bind_path = self._root_mount_dir / system_dir
                    self.unmount_device_or_directory(system_dir_bind_path, False)
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
            with open(self.path, "ab") as f:
                subprocess.run(["dd", "if=/dev/zero", "bs=1M", f"count={size_mo}"], stdout=f, check=True)
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
            logger.error(f"❌ root partition extention failed due to this error :\n {e}")
            self.unmount()
            exit(1)

    def extend_root_fs(self):
        self.map_partitions()
        self.unmount_image_partitions()
        logger.info(f"🔄 Extending root filesystem from {self.path}")
        try:
            e2fsck = subprocess.run(["e2fsck", "-f", self.root_partition], check=True, text=True).stdout
            logger.debug(f"e2fsck -f {self.root_partition} -> {e2fsck}")
            resize2fs = subprocess.run(["resize2fs", self.root_partition], check=True, text=True).stdout
            logger.debug(f"resize2fs {self.root_partition} -> {resize2fs}")
            logger.info("✅ root filesystem successfully extended")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ root filesystem extention failed due to this error :\n {e}")
            self.unmount()
            exit(1)

    def add_root_space(self, size_mo: int):
        self.extend_image(size_mo)
        self.extend_root_partition()
        self.extend_root_fs()

    def install_package_script(self, package_path: Path):
        self.bind_system_dirs()
        package_name = package_path.name
        install_script_path = package_path / "install.sh"
        logger.info(f"🔄 Installing {package_name} from script")
        try:
            install_script = subprocess.run(
                ["chroot", self._root_mount_dir, "/bin/bash", "-c", install_script_path],
                check=True,
                text=True
            ).stdout
            logger.debug(f"chroot {self._root_mount_dir} /bin/bash -c {install_script_path} -> {install_script}")
            logger.info(f"✅ {package_name} successfully installed !")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Installing {package_name} from script failed due to this error :\n {e}")
            self.unmount()
            exit(1)

    def add_space_packages_from_script(self, packages_dir: Path):
        info_file_path = packages_dir / "info.yaml"
        try:
            with open(info_file_path, "r", encoding="utf-8") as info_file:
                self.add_root_space(
                    int(yaml.safe_load(info_file).get("space_needed", 0))
                )
        except Exception as e:
            logger.error(
                f"❌ Can't found space needed for packages from scripts (no space added) due to this error :\n {e}"
            )

    def install_packages_from_scripts(self, packages_dir: Path):
        if not packages_dir.is_dir():
            value_error = ValueError(f"\"{packages_dir}\" is not a directory !")
            logger.error(f"❌ Can't install packages from scripts due to this error :\n {value_error}")
            self.unmount()
            raise value_error
        self.add_space_packages_from_script(packages_dir)
        self.bind_system_dirs()
        # Binding package dir in image file system
        if not self._mount_packages_dir.exists():
            mkdir(self._mount_packages_dir)
        self.mount_bind_directory(packages_dir, self._mount_packages_dir)
        for package in packages_dir.iterdir():
            if package.is_dir():
                self.install_package_script(
                    self._image_packages_dir / package.name
                )
        self.unmount_device_or_directory(self._mount_packages_dir)

    def customize_end_to_end(self, settings):
        self.install_packages_from_scripts(settings.PACKAGES_PATH)
        self.unmount()
