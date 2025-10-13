#!/usr/bin/env python3
import base64

# Obfuscated credentials hint
encoded_hint = "Y3JlZGVudGlhbHM6IGFkbWluL2MyOGMyMGM1YjE5YmM0Y2E1M2U0ZjU0YjA2ODA4ZTM0"
decoded = base64.b64decode(encoded_hint).decode()
print(f"Decoded hint: {decoded}")

# This script doesn't do much, but the encoded string is important