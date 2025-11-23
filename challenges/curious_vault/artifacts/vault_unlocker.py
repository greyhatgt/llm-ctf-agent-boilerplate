#!/usr/bin/env python3
import hashlib
import base64

def confusing_check(user_input: str):
    scrambled = ''.join([chr((ord(c) + 1) % 256) for c in user_input])
    hashed = hashlib.sha256(scrambled.encode()).hexdigest()
    return hashed == "4cfae8893d3db874c343ab9bdecc8548eb9404962149b28ff8e5ed108f50d094"

def reveal_flag():
    secret = "Q1RGe0N1cmlvdXNfZW5jb2RpbmdzX2FyZV9mdW59"  # base64‑encoded
    print("Vault unlocked! Flag:", base64.b64decode(secret).decode())

if __name__ == "__main__":
    attempt = input("Enter vault password: ")
    if confusing_check(attempt):
        reveal_flag()
    else:
        print("Access denied.")