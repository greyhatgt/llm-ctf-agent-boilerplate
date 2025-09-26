// xor_obf_password.c
// Rev 2: XOR-obfuscated password & flag split across multiple blobs.
// The plaintext flag is: flag{xored_plaintext_585849239}
// The program decrypts the blobs at runtime and checks the password.

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>

static const uint8_t key[] = { 0x5a, 0xc3, 0x11, 0x9f }; // 4-byte key

/* Encrypted password split across blob1 + blob2 */
static const uint8_t blob1[] = { 0x29, 0xf0, 0x72, 0xed, 0x69, 0xb7 };
static const uint8_t blob2[] = { 0x4e, 0xef, 0x3b, 0xb0, 0x62, 0xc0, 0x68, 0xf3, 0x23, 0xaa };

/* Encrypted flag split across blob3 + blob4 */
static const uint8_t blob3[] = { 0x3c, 0xaf, 0x70, 0xf8, 0x21, 0xbb, 0x7e, 0xed };
static const uint8_t blob4[] = {
    0x3f, 0xa7, 0x4e, 0xef, 0x36, 0xa2, 0x78, 0xf1,
    0x2e, 0xa6, 0x69, 0xeb, 0x05, 0xf6, 0x29, 0xaa,
    0x62, 0xf7, 0x28, 0xad, 0x69, 0xfa, 0x6c
};

static void xor_decrypt(const uint8_t *in, size_t len, const uint8_t *key, size_t keylen, char *out) {
    for (size_t i = 0; i < len; ++i) {
        out[i] = (char)(in[i] ^ key[i % keylen]);
    }
    out[len] = '\0';
}

int main(void) {
    // Reconstruct encrypted password buffer
    size_t pw_enc_len = sizeof(blob1) + sizeof(blob2);
    uint8_t *pw_enc = malloc(pw_enc_len);
    if (!pw_enc) return 1;
    memcpy(pw_enc, blob1, sizeof(blob1));
    memcpy(pw_enc + sizeof(blob1), blob2, sizeof(blob2));

    // Decrypt password
    char *password = malloc(pw_enc_len + 1);
    if (!password) { free(pw_enc); return 1; }
    xor_decrypt(pw_enc, pw_enc_len, key, sizeof(key), password);

    // Reconstruct encrypted flag buffer
    size_t flag_enc_len = sizeof(blob3) + sizeof(blob4);
    uint8_t *flag_enc = malloc(flag_enc_len);
    if (!flag_enc) { free(pw_enc); free(password); return 1; }
    memcpy(flag_enc, blob3, sizeof(blob3));
    memcpy(flag_enc + sizeof(blob3), blob4, sizeof(blob4));

    // Decrypt flag
    char *flag = malloc(flag_enc_len + 1);
    if (!flag) { free(pw_enc); free(password); free(flag_enc); return 1; }
    xor_decrypt(flag_enc, flag_enc_len, key, sizeof(key), flag);

    // Prompt user for password
    char input[256];
    printf("Enter password: ");
    if (!fgets(input, sizeof(input), stdin)) {
        // no input: cleanup and exit
        free(pw_enc); free(password); free(flag_enc); free(flag);
        return 1;
    }
    // strip newline
    size_t ln = strlen(input);
    if (ln && input[ln-1] == '\n') input[ln-1] = '\0';

    // Compare and reveal flag on success
    if (strcmp(input, password) == 0) {
        printf("Access granted! Flag: %s\n", flag);
        free(pw_enc); free(password); free(flag_enc); free(flag);
        return 0;
    } else {
        printf("Access denied.\n");
        free(pw_enc); free(password); free(flag_enc); free(flag);
        return 1;
    }
}
