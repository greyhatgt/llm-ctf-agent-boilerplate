#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

static inline uint8_t rotl8(uint8_t value, unsigned int shift) {
  shift &= 7u;
  if (shift == 0u) return value;
  return (uint8_t)((uint8_t)(value << shift) | (uint8_t)(value >> (8u - shift)));
}

static inline uint8_t rotr8(uint8_t value, unsigned int shift) {
  shift &= 7u;
  if (shift == 0u) return value;
  return (uint8_t)((uint8_t)(value >> shift) | (uint8_t)(value << (8u - shift)));
}

static uint32_t xorshift32(uint32_t *state) {
  uint32_t x = *state;
  x ^= x << 13;
  x ^= x >> 17;
  x ^= x << 5;
  *state = x;
  return x;
}

static uint32_t fnv1a32(const unsigned char *data, size_t len) {
  uint32_t h = 2166136261u;
  for (size_t i = 0; i < len; ++i) {
    h ^= (uint32_t)data[i];
    h *= 16777619u;
  }
  return h;
}

static void weird_transform(const char *input, char *output) {
  static const uint8_t sbox[16] = {
    0x0, 0xE, 0x7, 0xA, 0x4, 0xD, 0x1, 0x2,
    0xF, 0xB, 0x5, 0x9, 0xC, 0x8, 0x6, 0x3
  };
  static const char *hi_table = "QWERTYUIOPASDFGH";  /* 16 chars */
  static const char *lo_table = "JKLZXCVBNM012345";  /* 16 chars */

  size_t n = strlen(input);
  uint32_t seed = fnv1a32((const unsigned char *)input, n) ^ 0xA5F00D42u;
  if (seed == 0u) seed = 0xDEADBEEFu;  /* avoid zero state */

  for (size_t i = 0; i < n; ++i) {
    uint8_t b = (uint8_t)input[i];

    uint32_t rnd = xorshift32(&seed);
    uint8_t k0 = (uint8_t)rnd;
    uint8_t k1 = (uint8_t)(rnd >> 8);
    uint8_t k2 = (uint8_t)(rnd >> 16);

    uint8_t r = rotl8(b ^ k0, (unsigned)((i & 7u) + 1u));
    r ^= (uint8_t)(k1 + (uint8_t)(i * 31u));

    uint8_t odd = (uint8_t)(r & 0xAAu);
    uint8_t even = (uint8_t)(r & 0x55u);
    r = (uint8_t)((odd >> 1) | (even << 1));

    r = (uint8_t)(((r & 0x33u) << 2) | ((r & 0xCCu) >> 2));
    r = rotr8(r, (unsigned)(((k2 >> 3) & 7u) + 1u));

    r = (uint8_t)((sbox[(r >> 4) & 0xFu] << 4) | sbox[r & 0xFu]);
    r ^= (uint8_t)(0x5Au ^ (uint8_t)(i * 0x1Fu));

    output[2 * i] = hi_table[(r >> 4) & 0xF];
    output[2 * i + 1] = lo_table[r & 0xF];
  }

  output[2 * n] = '\0';
}

int main(int argc, char **argv) {
  const char *msg = NULL;
  if (argc > 1) {
    msg = argv[1];
  }

  size_t len = strlen(msg);
  char *out = (char *)malloc(len * 2 + 1);
  if (!out) {
    fprintf(stderr, "allocation failed\n");
    return 1;
  }

  weird_transform(msg, out);
  puts(out);
  free(out);
  return 0;
}


