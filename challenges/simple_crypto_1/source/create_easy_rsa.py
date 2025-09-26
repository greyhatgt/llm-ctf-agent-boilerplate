#!/usr/bin/env python3
import secrets
from pathlib import Path

# ----------------- utilities -----------------
def is_probable_prime(n, k=8):
    if n < 2: return False
    small_primes = [2,3,5,7,11,13,17,19,23,29]
    for p in small_primes:
        if n % p == 0:
            return n == p
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(k):
        a = secrets.randbelow(n - 3) + 2
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True

def gen_prime(bits):
    while True:
        p = secrets.randbits(bits) | (1 << (bits - 1)) | 1
        if is_probable_prime(p):
            return p

# ----------------- challenge params -----------------
FLAG = "flag{easy_rsa_283472384}"

# Determine output directory relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
ART = SCRIPT_DIR.parent / "artifacts"
ART.mkdir(parents=True, exist_ok=True)

# Generate small primes (32-bit)
p = gen_prime(32)
q = gen_prime(32)
while q == p:
    q = gen_prime(32)

N = p * q
e = 65537
m = int.from_bytes(FLAG.encode(), "big")
c = pow(m, e, N)

# Write challenge
with open(ART / "challenge.txt", "w") as f:
    f.write("# easy RSA factoring challenge\n")
    f.write(f"N = {N}\n")
    f.write(f"e = {e}\n")
    f.write(f"c = {c}\n")
    f.write("\n# Goal: factor N or recover the plaintext flag.\n")
    f.write("flag format: CTF{...}\n")

# Write maintainer solution
with open(ART / "solution.txt", "w") as f:
    f.write("MAINTAINER SOLUTION (do not ship)\n")
    f.write(f"p = {p}\nq = {q}\n")
    f.write(f"flag = {FLAG}\n")
