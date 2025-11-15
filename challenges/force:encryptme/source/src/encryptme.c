#include <stdio.h>
#include <string.h>
#include <ctype.h>

// Function to decrypt a single character
char decrypt_char(char c, char key) {
    if (isupper(c)) {
        return ((c - key + 26) % 26) + 'A';
    } else if (islower(c)) {
        return ((c - key + 26) % 26) + 'a';
    } else {
        return c; // Return non-alphabetic characters as is
    }
}

// Simple decrypt Vigenere
void decrypt(char *encrypted, char *key, char *decrypted) {
    int keyLength = strlen(key);
    int keyIndex = 0;

    for (int i = 0; encrypted[i] != '\0'; i++) {
        if (isalpha(encrypted[i])) {
            decrypted[i] = decrypt_char(encrypted[i], tolower(key[keyIndex]) - 'a');
            keyIndex = (keyIndex + 1) % keyLength;
        } else {
            decrypted[i] = encrypted[i]; // Keep non-alphabet characters as is
        }
    }
    decrypted[strlen(encrypted)] = '\0';
}

int main() {
    setreuid(geteuid(), geteuid());
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    char encrypted[] = "vbaiy{Wnfttcimrjpgu.efk}";
    char key[] = "crypto";
    char decrypted[100];

    printf("The encrypted flag: ");

    printf("The decrypted flag: %s\n", encrypted);
    return 0;
}
