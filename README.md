# OSImagePrepper

## Description
This project was initially started to build custom images for Raspberry Pi but can also be used to create other images.
It uses Docker to avoid dependency issues or simply to prevent the need for installing them on your system, making it easier to use in CI/CD pipelines.

## Usage
```yaml
# File : docker-compose.yml
version: '3.8'

services:
  your_service_name:
    image: nemesix493/os-image-prepper
    privileged: true

    volumes:
      - <data_dir_path>:/workspace/data
    
    environment:
      BASE_IMAGE_PATH: "your_base_image_path"  # Relative path from data volume. Default: base_img.img
      FINAL_IMAGE_NAME: "your_final_image_name"  # Default: new-image
      KEEP_BASE_IMAGE: 0 or 1  # 0 to erase the base image with the new one. Default: 1
      PACKAGES_DIR: "path_to_your_packages_directory"  # Relative path from "/workspace/data/". Default: packages
```
### Explanation:

- In `<data_dir_path>`, place your source image. The prepared image will be saved in a directory named after the value of the `FINAL_IMAGE_NAME` environment variable.

- In `path_to_your_packages_directory`, place the packages you want to install in the prepared image. Each package must be a directory, with an `install.sh` script inside, e.g., `package_name/install.sh`.

- In `path_to_your_packages_directory`, place a YAML file named `info.yaml`. This file must include the property `space_needed`, which specifies the total disk space required (in MB) to install all your packages. For example, if 100 MB of space is needed, the `info.yaml` file should look like this:
    ```yaml
    # File : info.yaml
    space_needed: 100
    ```

⚠️ Recommendation: It's better not to use the `PACKAGES_DIR` variable directly. Instead, bind a volume from your package directory into `/workspace/data/packages`, as shown below:

```yaml
# File : docker-compose.yml
version: '3.8'

services:
  your_service_name:
    image: nemesix493/os-image-prepper
    privileged: true

    volumes:
      - <data_dir_path>:/workspace/data
      - <path_to_your_packages_directory>:/workspace/data/packages
    
    environment:
      BASE_IMAGE_PATH: "your_base_image_path"  # Relative path from data volume. Default: base_img.img
      FINAL_IMAGE_NAME: "your_final_image_name"  # Default: new-image
      KEEP_BASE_IMAGE: 0 or 1  # 0 to erase the base image with the new one. Default: 1

```

## Supported Inputs

Currently, the only supported input image formats are `.img` and `.img.xz`.
