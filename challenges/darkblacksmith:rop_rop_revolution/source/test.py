#!/usr/bin/env python3
from pwn import *
import os

ROOT = os.path.abspath(os.path.dirname(__file__))
context.arch = "x86_64"
context.bits = 32

bin = os.path.join(ROOT, "../docker/target")

def run_simple_test(process_name):
    """
    Test the binary for buffer overflow by sending an oversized payload
    and checking for a segmentation fault.
    """
    with process(process_name) as proc:
        proc.recvuntil(b"Enter your Steps of the YMCA Song:")
        # Send oversized payload
        proc.sendline(b"A" * 1000)
        
        # Wait for the process to terminate
        proc.wait()
        
        # Check for segmentation fault (exit code -11)
        if proc.poll() == -11:
            print("Test passed: Segmentation fault (SIGSEGV) detected!")
        else:
            print(f"Test failed: Process exited with code {proc.poll()}")

if __name__ == "__main__":
    if "REMOTE" in os.environ:
        if not "PORT" in os.environ:
            print("[!] Please specify the port number")
            exit(1)
        p = remote("localhost", int(os.environ["PORT"]))
    else:
        b = os.path.abspath(bin)
        p = process(b, cwd=os.path.dirname(b))
    
    run_simple_test(bin)

