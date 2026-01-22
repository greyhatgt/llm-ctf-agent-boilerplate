import imageio
import numpy as np

flag = "flag{hell0_l00Ks_l1k3_y0u_f0uNd_1t}"
cover_path = "stego_hello.png"
stego_path = "stego_hello_embedded.png"

# Convert text to bits with 32-bit length header
def text_to_bits(s):
    b = s.encode("utf-8")
    length = len(b)
    header = length.to_bytes(4, byteorder="big")
    data = header + b
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7-i)) & 1)
    return bits

bits = text_to_bits(flag)

# Load cover image
img = imageio.imread(cover_path)
h, w, c = img.shape
capacity = h * w  # 1 bit per pixel in blue channel
if len(bits) > capacity:
    raise ValueError("Image too small for flag!")

# Flatten blue channel and embed bits
flat_blue = img[:,:,2].flatten()  # RGB, blue channel
for i, b in enumerate(bits):
    flat_blue[i] = (flat_blue[i] & 0xFE) | b
img[:,:,2] = flat_blue.reshape((h,w))

# Save stego image
imageio.imwrite(stego_path, img)
print("Stego image saved to:", stego_path)