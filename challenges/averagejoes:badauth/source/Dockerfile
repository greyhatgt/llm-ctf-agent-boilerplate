from ubuntu:22.04

RUN adduser --disabled-password --gecos '' ctf

# enable 32-bit support + pwntool
RUN dpkg --add-architecture i386
RUN apt update
RUN apt install -y libc6:i386 libstdc++6:i386 \
    build-essential gcc-multilib g++-multilib \
    python3 python3-pip python3-dev git libssl-dev libffi-dev

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --upgrade pwntools

