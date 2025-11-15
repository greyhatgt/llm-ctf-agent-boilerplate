FROM ubuntu:22.04

RUN adduser --disabled-password --gecos '' ctf

# enable 32-bit support
RUN dpkg --add-architecture i386
# install packages
RUN apt update -y && \
    apt install -y libc6:i386 libstdc++6:i386 python3 python3-pip socat

# put other python libs you need here, for example:
RUN pip install z3

# copy service/flag files
COPY target.py /target.py

# make the target executable
RUN chmod +x /target.py

# use ctf user instead of root
USER ctf

# run socat
CMD ["socat", "-T60", "TCP-LISTEN:9217,bind=0.0.0.0,reuseaddr,fork", "EXEC:timeout 60 python3 /target.py"]
