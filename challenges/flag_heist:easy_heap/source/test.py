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
    try:
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"1")
        p.recvline()
        p.sendline(b"64")
        p.recvline()
        p.sendline(b"A" * 62)
        p.recvuntil(b"Success\n")
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"1")
        p.recvline()
        p.sendline(b"64")
        p.recvline()
        p.sendline(b"B" * 62)
        p.recvuntil(b"Success\n")
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"1")
        p.recvline()
        p.sendline(b"64")
        p.recvline()
        p.sendline(b"C" * 62)
        p.recvuntil(b"Success\n")
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"6")
        p.recvuntil(b"Success : Select previous entry\n")
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"5")
        p.recvuntil(b"Success : Select next entry\n")
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"6")
        p.recvuntil(b"Success : Select previous entry\n")
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"3")
        p.recvline()
        p.sendline(b"64")
        p.recvline()
        p.sendline(b"D" * 62)
        p.recvuntil(b"Success : Change current entry\n")
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"4")
        p.recvline()
        p.recvline()
        if p.recvline() != b"D" * 62 + b"\n":
            print("FAILED!")
            exit(1)
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"2")
        p.recvuntil(b"Success : Remove current entry\n")
        p.recvuntil(b"7. Exit\n")
        p.sendline(b"7")
        if b"Failed to get flag\n" == p.recvall():
            print("OK!")
            exit(0)
        else:
            print("FAILED!")
            exit(1)
    except Exception:
        print("FAILED!")
        exit(1)
