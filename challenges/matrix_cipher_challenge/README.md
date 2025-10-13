# Matrix Cipher Challenge

# This challenge encrypts a flag using a matrix transformation modulo 256. The  task is to reverse the transformation and recover the original flag.

The encryption uses a 4×4 key matrix and multiplies it with blocks of the plaintext flag. The result is saved as a NumPy `.npy` file.


#Files
- `artifacts/encrypted.npy`: Encrypted flag stored as a NumPy array.
- `source/decrypt_matrix.py`: Solver script to decrypt the flag using matrix inversion.
- `challenge.json`: Metadata and configuration for the challenge.

