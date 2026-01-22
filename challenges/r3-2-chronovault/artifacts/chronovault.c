#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>


static const uint8_t FLAG_CHECK_BYTECODE[] = {
    // opcode set (1 byte each) with optional operand bytes
    // Opcodes:
    // 0x01: LOAD_INPUT idx       -> reg = inputs[idx]
    // 0x02: ADD_IMM val          -> reg = reg + val
    // 0x03: XOR_SHIFT val        -> reg = reg ^ (val)
    // 0x04: ADD_CLOCK_FROM_REG   -> clock += reg
    // 0x05: MOD_IMM val          -> clock = clock % val
    // 0x06: XOR_CLOCK val        -> clock ^= val
    // 0x07: CMP_EQ_IMM val       -> if(clock == val) jump +2 (skip next instr)
    // 0xff: HALT

    // program (hand-crafted):
    0x01, 0x00,       // LOAD_INPUT 0   (reg = in0)
    0x02, 0x03,       // ADD_IMM 3      (reg += 3)
    0x04,             // ADD_CLOCK_FROM_REG (clock += reg)

    0x01, 0x01,       // LOAD_INPUT 1
    0x03, 0x02,       // XOR_SHIFT 2    (reg ^= 2)
    0x04,             // ADD_CLOCK_FROM_REG (clock += reg)

    0x05, 0x11,       // MOD_IMM 17     (clock %= 17)

    0x01, 0x02,       // LOAD_INPUT 2
    0x02, 0x05,       // ADD_IMM 5      (reg += 5)
    0x06, 0x2a,       // XOR_CLOCK 42   (clock ^= 42)
    0x04,             // ADD_CLOCK_FROM_REG (clock += reg)

    0x01, 0x03,       // LOAD_INPUT 3
    0x03, 0x01,       // XOR_SHIFT 1    (reg ^= 1)
    0x02, 0x07,       // ADD_IMM 7      (reg += 7)
    0x06, 0x00,       // XOR_CLOCK 0    (no-op placeholder)
    0x04,             // ADD_CLOCK_FROM_REG (clock += reg)

    0x05, 0xff,       // MOD_IMM 255    (final clamp)
    0x07, 0x7b,       // CMP_EQ_IMM 123 -> if(clock==123) skip next
    0xFF              // HALT
};

int clock_func(const uint8_t *bytecode, size_t len, int inputs[4], int *out_clock)
{
    int ip = 0;
    int reg = 0;
    int clock = 0;

    while (ip < (int)len) {
        uint8_t op = bytecode[ip++];
        switch (op) {
            case 0x01: { // LOAD_INPUT idx
                if (ip >= (int)len) return -1;
                uint8_t idx = bytecode[ip++];
                if (idx >= 4) return -1;
                reg = inputs[idx];
                break;
            }
            case 0x02: { // ADD_IMM val
                if (ip >= (int)len) return -1;
                uint8_t v = bytecode[ip++];
                reg = reg + (int)v;
                break;
            }
            case 0x03: { // XOR_SHIFT val
                if (ip >= (int)len) return -1;
                uint8_t v = bytecode[ip++];
                reg = reg ^ (int)v;
                break;
            }
            case 0x04: { // ADD_CLOCK_FROM_REG
                clock += reg;
                break;
            }
            case 0x05: { // MOD_IMM val
                if (ip >= (int)len) return -1;
                uint8_t v = bytecode[ip++];
                if (v == 0) return -1;
                clock = clock % (int)v;
                break;
            }
            case 0x06: { // XOR_CLOCK val
                if (ip >= (int)len) return -1;
                uint8_t v = bytecode[ip++];
                clock ^= (int)v;
                break;
            }
            case 0x07: { // CMP_EQ_IMM val  (if equal, skip next instruction byte)
                if (ip >= (int)len) return -1;
                uint8_t v = bytecode[ip++];
                if (clock == (int)v) {
                    // intentionally advance ip by 1 to skip the next opcode
                    if (ip < (int)len) ip++;
                }
                break;
            }
            case 0xFF: // HALT
                if (out_clock) *out_clock = clock;
                return 0;
            default:
                return -1;
        }
    }
    if (out_clock) *out_clock = clock;
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 5) {
        fprintf(stderr, "Usage: %s in0 in1 in2 in3\nEach input should be a small integer (0..31 recommended)\n", argv[0]);
        return 2;
    }

    int inputs[4];
    for (int i = 0; i < 4; ++i) inputs[i] = atoi(argv[i+1]);

    int clock = 0;
    int r = clock_func(FLAG_CHECK_BYTECODE, sizeof(FLAG_CHECK_BYTECODE), inputs, &clock);
    if (r != 0) {
        fprintf(stderr, "VM error\n");
        return 3;
    }

    if (clock == 123) {
        FILE *f = fopen("challenges/r3-2-chronovault/source/flag.txt", "r");
        if (f) {
            char buf[1024];
            if (fgets(buf, sizeof(buf), f)) {
                printf("%s", buf);
            }
            fclose(f);
        } else {
            fprintf(stderr, "flag file not found\n");
        }
        return 0;
    } else {
        printf("Clock = %d -- nothing to see.\n", clock);
        return 1;
    }
}
