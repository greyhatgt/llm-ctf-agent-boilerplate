#!/usr/bin/env python3

import os
import re
import sys

from pwn import *

ROOT = os.path.abspath(os.path.dirname(__file__))

context.arch = "x86_64"
context.bits = 32

bin = os.path.join(ROOT, "../docker/target")

if __name__ == '__main__':
    if "REMOTE" in os.environ:
        if not "PORT" in os.environ:
            print("[!] Please specify the port number")
            exit(1)
        p = remote("localhost", int(os.environ["PORT"]))
    else:
        b = os.path.abspath(bin)
        p = process(b, cwd=os.path.dirname(b))

    p.sendline(b"250382")
    if b"Password OK :)" in p.recvall():
        print("OK!")
        exit(0)
    else:
        print("FAILED!")
        exit(1)
