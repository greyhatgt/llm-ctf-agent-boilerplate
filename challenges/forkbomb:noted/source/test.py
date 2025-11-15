#!/usr/bin/env python3

import os
import base64
from pwn import *

ROOT = os.path.abspath(os.path.dirname(__file__))
context.arch = "x86_64"

def perform_check(p):
    # Try to create a simple note
    test_filename = "test.txt"
    test_content = "hello world"

    # Create note
    p.sendlineafter(b"Choice: ", b"1")
    p.sendlineafter(b"filename: ", test_filename.encode())
    p.sendlineafter(b"content: ", test_content.encode())

    # Try to view the note
    p.sendlineafter(b"Choice: ", b"2")
    encoded_filename = base64.b64encode(test_filename.encode())
    p.sendlineafter(b"view: ", encoded_filename)

    # Get response
    response = p.recvuntil(b"===")

    # Check if our test content is in the response
    if test_content.encode() in response:
        print("[+] Basic functionality check: OK!")
        return True
    else:
        print("[-] Basic functionality check: FAILED!")
        print("[-] Expected to find:", test_content)
        print("[-] Got response:", response)
        return False

if __name__ == '__main__':
    try:
        if "REMOTE" in os.environ:
            if not "PORT" in os.environ:
                print("[!] Please specify the port number")
                exit(1)
            p = remote("localhost", int(os.environ["PORT"]))
        else:
            p = process('./challenge')

        # Perform the check
        if perform_check(p):
            p.close()
            exit(0)
        else:
            p.close()
            exit(1)

    except Exception as e:
        print(f"[-] Error during check: {e}")
        exit(1)
