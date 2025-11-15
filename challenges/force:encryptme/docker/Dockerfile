FROM ubuntu:22.04

RUN adduser --disabled-password --gecos '' ctf

# enable 32-bit support
RUN dpkg --add-architecture i386
RUN apt update
RUN apt install -y libc6:i386 libstdc++6:i386

# install packages
RUN apt install -y socat

# copy service/flag files
COPY flag /flag
COPY target /target

# make the flag readonly
RUN chmod 444 /flag

RUN chmod 755 /target

# use ctf user instead of root
USER ctf

# run socat
CMD ["socat", "-T60", "TCP-LISTEN:9999,reuseaddr,fork", "EXEC:timeout 60 /target"]
