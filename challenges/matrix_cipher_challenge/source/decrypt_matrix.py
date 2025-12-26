# decrypt_matrix.py
import numpy as np
from numpy.linalg import inv

# Load encrypted data
C = np.load("artifacts/encrypted.npy")

# Key matrix
K = np.array([[3, 5, 2, 7],
              [1, 1, 4, 2],
              [6, 3, 5, 1],
              [2, 7, 1, 3]], dtype=np.uint8)

# Invert matrix mod 256
def modinv_matrix(K, mod):
    K_inv = inv(K)
    K_inv_int = np.round(K_inv).astype(int)
    return K_inv_int % mod

K_inv = modinv_matrix(K, 256)

# Decrypt
P = (K_inv @ C) % 256
plaintext = P.T.flatten().astype(np.uint8).tobytes().rstrip()

print("Decrypted flag:", plaintext.decode())
