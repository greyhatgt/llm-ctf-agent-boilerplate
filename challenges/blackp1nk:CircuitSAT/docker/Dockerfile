FROM ubuntu:22.04

# Create a non-root user
RUN adduser --disabled-password --gecos '' ctf

# Enable 32-bit support
RUN dpkg --add-architecture i386
RUN apt update -y && \
    apt install -y libc6:i386 libstdc++6:i386 python3 python3-pip socat git

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install z3-solver==4.13.0.0


# Copy the service and flag files
COPY docker/flag /flag

# Create /src directory and copy remote_chall.py into it
RUN mkdir -p /src
# COPY source/src/remote_chall.py /src/remote_chall.py
COPY source/src/ /src/


# Make the flag file read-only
RUN chmod a-w /flag
RUN chmod +x /src/remote_chall.py

# Use the ctf user instead of root
USER ctf

# Set the command to run the Python script
CMD ["socat", "-T60", "TCP-LISTEN:9218,bind=0.0.0.0,reuseaddr,fork", "EXEC:python3 /src/remote_chall.py"]
