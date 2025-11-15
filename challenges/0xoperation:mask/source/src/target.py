#!/usr/bin/env python3
import time
import sys

def main():
    correct_str = '01110100010101000001011111010101'
    bit_string = input(f"Enter your 32-bit password (e.g., 01010101010101010101010101010101). Remember, it needs to map to {correct_str}! Hint: a ^ b = c!\n")

    if len(bit_string) != 32 or not all(c in '01' for c in bit_string):
        print("Invalid input! Please enter exactly 32 bits (0s and 1s only).")
        return

    api_key = '11101011101011011010101011011010'

    final_str = ''
    for i in range(32):
        if api_key[i] == '0':
            time.sleep(0.1)
            print(f"{i + 1} out of 32 of the way done!")
            sys.stdout.flush()
            temp = int(bit_string[i]) ^ int(api_key[i])
            final_str += (str(temp))
        else:
            time.sleep(.2)
            temp = int(bit_string[i]) ^ int(api_key[i])
            final_str += str(temp)
            print(f"{i + 1} out of 32 of the way done!")
            sys.stdout.flush()

    if final_str == correct_str:
        bit_string = input(f"Please enter your bank account number: \n")
        bit_string = input(f"Please enter your bank account number: \n")
        print("tkctf{y0u_h4ck3d_th3_g4m3}")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
