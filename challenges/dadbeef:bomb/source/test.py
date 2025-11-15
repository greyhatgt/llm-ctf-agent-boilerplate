#!/usr/bin/env python3

import os
from pwn import *

ROOT = os.path.abspath(os.path.dirname(__file__))

# Set the correct architecture and bitness
context.arch = "i386"
context.bits = 32

bin_path = os.path.join(ROOT, "../docker/target")

def exploit(p):
    # Send the first input (password)
    p.sendline("or this?")
    # Send the second input (number)
    p.sendline("191")
    # Receive all output
    output = p.recvall(timeout=2)
    # Check for success conditions in the output
    if b"another password?\n" in output:
        print("OK!")
        exit(0)
    else:
        print("FAILED!")
        exit(1)

if __name__ == '__main__':
    if "REMOTE" in os.environ:
        if not "PORT" in os.environ:
            print("[!] Please specify the port number")
            exit(1)
        p = remote("localhost", int(os.environ["PORT"]))
    else:
        b = os.path.abspath(bin_path)
        # Ensure the current working directory is set correctly
        p = process(b, cwd=os.path.dirname(b))

    exploit(p)