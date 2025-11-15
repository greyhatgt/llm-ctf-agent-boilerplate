#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <ctype.h>
#include <stdint.h>

#define MAX_NOTE_SIZE 256
#define MAX_NOTES 5

// Base64 encoding table
static const char base64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

void setup() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

size_t base64_encode(const char *src, char *dst, size_t len) {
    size_t i, j;
    uint8_t buf[3];
    uint8_t tmp[4];

    for (i = 0, j = 0; i < len; i += 3) {
        buf[0] = src[i];
        buf[1] = ((i+1) < len) ? src[i+1] : 0;
        buf[2] = ((i+2) < len) ? src[i+2] : 0;

        tmp[0] = (buf[0] >> 2) & 0x3F;
        tmp[1] = ((buf[0] << 4) | (buf[1] >> 4)) & 0x3F;
        tmp[2] = ((buf[1] << 2) | (buf[2] >> 6)) & 0x3F;
        tmp[3] = buf[2] & 0x3F;

        dst[j++] = base64_table[tmp[0]];
        dst[j++] = base64_table[tmp[1]];
        dst[j++] = (i+1 < len) ? base64_table[tmp[2]] : '=';
        dst[j++] = (i+2 < len) ? base64_table[tmp[3]] : '=';
    }
    dst[j] = '\0';
    return j;
}

size_t base64_decode(const char *src, char *dst) {
    size_t i, j = 0;
    uint8_t a, b, c, d;
    size_t len = strlen(src);

    for (i = 0; i < len; i += 4) {
        // Get values for each base64 character
        a = strchr(base64_table, src[i]) - base64_table;
        b = strchr(base64_table, src[i+1]) - base64_table;
        c = (src[i+2] == '=') ? 0 : strchr(base64_table, src[i+2]) - base64_table;
        d = (src[i+3] == '=') ? 0 : strchr(base64_table, src[i+3]) - base64_table;

        dst[j++] = (a << 2) | (b >> 4);
        if (src[i+2] != '=')
            dst[j++] = (b << 4) | (c >> 2);
        if (src[i+3] != '=')
            dst[j++] = (c << 6) | d;
    }
    dst[j] = '\0';
    return j;
}

void read_input(char *buf, size_t size) {
    if (!fgets(buf, size, stdin)) {
        exit(1);
    }
    size_t len = strlen(buf);
    if (len > 0 && buf[len-1] == '\n') {
        buf[len-1] = '\0';
    }
}

void debug_print(const char *format) {
    // Vulnerable: Format string bug
    printf(format);
}

void view_note() {
    char filename[64];
    char command[512];
    char decoded[128];

    printf("Enter note filename to view: ");
    read_input(filename, sizeof(filename));

    if(strncmp(filename, "DEBUG:", 6) == 0) {
        debug_print(filename + 6);
        return;
    }

    // Base64 decode the filename
    base64_decode(filename, decoded);

    snprintf(command, sizeof(command), "cat /home/ctf/notes/%s", decoded);
    system(command);
}

void create_note() {
    char filename[64];
    char content[MAX_NOTE_SIZE];
    char command[512];
    char encoded[128];

    printf("Enter note filename: ");
    read_input(filename, sizeof(filename));

    printf("Enter note content: ");
    read_input(content, sizeof(content));

    // Base64 encode the filename
    base64_encode(filename, encoded, strlen(filename));

    snprintf(command, sizeof(command),
             "mkdir -p /home/ctf/notes && echo '%s' > /home/ctf/notes/%s",
             content, filename);
    system(command);

    printf("Note saved as: %s\n", encoded);
}

void delete_note() {
    char filename[64];
    char command[512];
    char decoded[128];

    printf("Enter note filename to delete: ");
    read_input(filename, sizeof(filename));

    // Base64 decode the filename
    base64_decode(filename, decoded);

    snprintf(command, sizeof(command), "rm /home/ctf/notes/%s", decoded);
    system(command);

    printf("Note deleted!\n");
}

void print_menu() {
    printf("\n=== Secret Note Manager V2 ===\n");
    printf("1. Create Note\n");
    printf("2. View Note\n");
    printf("3. Delete Note\n");
    printf("4. Exit\n");
    printf("Choice: ");
}

int main() {
    char choice[8];
    setup();

    while(1) {
        print_menu();
        read_input(choice, sizeof(choice));

        switch(atoi(choice)) {
            case 1:
                create_note();
                break;
            case 2:
                view_note();
                break;
            case 3:
                delete_note();
                break;
            case 4:
                printf("Goodbye!\n");
                return 0;
            default:
                printf("Invalid choice!\n");
                break;
        }
    }

    return 0;
}
