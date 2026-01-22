//song.c
//A very simple reverse engineering challenge

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>

static const uint8_t KEY = 0x67; // xor key

//Encoded Flag
//The actual plaintext flag is: flag{l3sten_t3_th5s_s0ng_r1ght_n0w}
static const uint8_t enc_flag[] = {0x1, 0xc, 0x8, 0x3, 0x20, 0x10, 0x5a, 0x1b, 0x1b, 0xb, 0x13, 0x43, 0x1f, 0x61, 0x46, 0x22, 0x1f, 0x63, 0x26,
0x4b, 0x28, 0x6c, 0x1f, 0x17, 0x50, 0x2e, 0x70, 0x1b, 0x2b, 0x30, 0x56, 0x28, 0x77, 0x31, 0x3c};

static const size_t len = sizeof(enc_flag);

// enc[i] = ((flag[i] ^ KEY) + i) & 0xFF
void decrypt_flag(uint8_t *mix) {
    for (size_t i = 0; i < len; i++) {
        uint8_t a = enc_flag[i];
        uint8_t d = (uint8_t)(a - i);
        mix[i] = d ^ KEY;
    }
}

int main(void) {
    puts("When rev ever, where rev ever... ");
    printf("Sing it with me: ");

    char input[128];
    if (!fgets(input, sizeof(input), stdin)) {
        return 1;
    }

    size_t ln = strlen(input);
    if (ln > 0 && input[ln-1] == '\n') {
        input[ln-1] = '\0';
    }

    uint8_t flag[128];
    decrypt_flag(flag);
    flag[len] = 0;

    if (strcmp((char*)flag, input) == 0) {
        puts("Correct! You are good at singing");
    } else {
        puts("Eh, please get auto-tuned");
    }

    return 0;
}

