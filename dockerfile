FROM debian:latest

WORKDIR /workspace

RUN apt update && apt install -y \
    qemu-user-static \
    binfmt-support \
    debootstrap \
    fdisk \
    mount \
    sudo \
    kmod \
    unzip \
    xz-utils \
    kpartx \
    parted
RUN apt install -y python3 python3-pip python3-venv

COPY . /workspace/

RUN python3 -m venv env
RUN ./env/bin/pip install --no-cache-dir -r ./requirements.txt

CMD ["./env/bin/python", "-m", "run"]