#!/usr/bin/env python3
"""
verify_easy.py

Usage:
  python3 verify_easy.py path/to/challenge.txt "CTF{...}"

Reads N,e,c from challenge.txt and checks whether the provided flag
encrypts to c under the given N and e.

Exit code: 0 for correct, 1 for incorrect.
"""
import sys
from pathlib import Path

def read_challenge(path):
    N = e = c = None
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            if line.startswith("N ="):
                N = int(line.split("=",1)[1].strip())
            elif line.startswith("e ="):
                e = int(line.split("=",1)[1].strip())
            elif line.startswith("c ="):
                c = int(line.split("=",1)[1].strip())
    if None in (N,e,c):
        raise ValueError("Could not parse N, e, c from challenge file")
    return N,e,c

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 verify_easy.py path/to/challenge.txt \"flag{...}\"")
        sys.exit(2)
    path = Path(sys.argv[1])
    candidate = sys.argv[2]
    N,e,c = read_challenge(path)

    m = int.from_bytes(candidate.encode(), "big")
    c2 = pow(m, e, N)
    if c2 == c:
        print("CORRECT")
        sys.exit(0)
    else:
        print("INCORRECT")
        sys.exit(1)
