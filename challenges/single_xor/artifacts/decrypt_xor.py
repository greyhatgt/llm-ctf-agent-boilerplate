#!/usr/bin/env python3
# decrypt_xor.py
# Usage: python3 decrypt_xor.py ciphertext.hex

import sys
import binascii
import re

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 decrypt_xor.py ciphertext.hex")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "rb") as f:
        hexdata = f.read().strip()
    try:
        data = binascii.unhexlify(hexdata)
    except Exception as e:
        print("Failed to decode hex:", e)
        sys.exit(1)

    flag_re = re.compile(rb"flag\{\S+\}")

    for k in range(256):
        plain = bytes([b ^ k for b in data])
        if flag_re.search(plain):
            print(f"Found key: 0x{k:02x} ({k})")
            print("Plaintext:", plain.decode(errors='replace'))
            return

    print("No matching key found.")

if __name__ == "__main__":
    main()
