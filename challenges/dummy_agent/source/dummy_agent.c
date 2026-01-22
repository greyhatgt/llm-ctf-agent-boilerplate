#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h> 

void print_help();
void list_files();
void read_file_command(char *args);
void set_apikey(char *args);
void login();

char* base64_decode(const char* data, size_t input_length, size_t *output_length);
void reverse_string(char *str);
void xor_decrypt(char *input, const char *key);

bool api_key_set = false;

int main() {
    char input[100];
    char *command;
    char *args;

    printf("Welcome to the Dummy AI Agent!\n");
    printf("Type 'help' to see a list of commands.\n");

    while (1) {
        printf("> ");
        fgets(input, 100, stdin);
        input[strcspn(input, "\n")] = 0;

        command = strtok(input, " ");
        args = strtok(NULL, "");

        if (strcmp(command, "help") == 0) {
            print_help();
        } else if (strcmp(command, "list_files") == 0) {
            list_files();
        } else if (strcmp(command, "read_file") == 0) {
            read_file_command(args);
        } else if (strcmp(command, "set-apikey") == 0) {
            set_apikey(args);
        } else if (strcmp(command, "login") == 0) {
            login();
        } else if (strcmp(command, "exit") == 0) {
            break;
        } else {
            printf("Unknown command: %s\n", command);
        }
    }

    return 0;
}

void print_help() {
    printf("Available commands:\n");
    printf("  help        - Print this help message\n");
    printf("  list_files  - List files in the current directory\n");
    printf("  read_file   - Read the content of a file\n");
    printf("  exit        - Exit the agent\n");
}

void list_files() {
    printf("main.c\n");
    printf("README.md\n");
}

void read_file_command(char *args) {
    if (args == NULL) {
        printf("Usage: read_file <filename>\n");
        return;
    }
    printf("Reading file: %s\n", args);
    printf("Permission denied.\n");
}

void set_apikey(char *args) {
    if (args == NULL) {
        printf("Usage: set-apikey <apikey>\n");
        return;
    }

    char encrypted_api_key[] = { 0x20, 0x3d, 0x2e, 0x12, 0x34, 0x25, 0x15, 0x07, 0x36, 0x48, 0x54, 0x09, 0x3e, 0x22, 0x3c, 0x19, 0x2c, 0x5a, 0x09, 0x37, 0x39, 0x2f, 0x3d, 0x20, 0x00 };
    char *key = "mykey";

    xor_decrypt(encrypted_api_key, key);
    size_t decoded_len;
    char *base64_decoded = base64_decode(encrypted_api_key, strlen(encrypted_api_key), &decoded_len);
    reverse_string(base64_decoded);

    if (strcmp(args, base64_decoded) == 0) {
        printf("API key set successfully!\n");
        api_key_set = true;
    } else {
        printf("Invalid API key.\n");
    }
    free(base64_decoded);
}

void login() {
    if (api_key_set) {
        char flag_part1_obf[] = { 0x15, 0x09, 0x02, 0x15, 0x1e, 0x00 };
        char flag_part2_obf[] = { 0x04, 0x56, 0x0f, 0x11, 0x55, 0x19, 0x16, 0x00 };
        char flag_part3_obf[] = { 0x2c, 0x11, 0x53, 0x2d, 0x11, 0x1c, 0x40, 0x00 };
        char flag_part4_obf[] = { 0x2c, 0x01, 0x16, 0x1f, 0x08, 0x0d, 0x2c, 0x51, 0x04, 0x41, 0x00}; 
        char flag_part5_obf[] = { 0x1d, 0x11, 0x1e, 0x00}; 
        char *key = "secret";

        xor_decrypt(flag_part1_obf, key);
        xor_decrypt(flag_part2_obf, key);
        xor_decrypt(flag_part3_obf, key);
        xor_decrypt(flag_part4_obf, key);
        xor_decrypt(flag_part5_obf, key);

        char flag[100];
        strcpy(flag, flag_part1_obf);
        strcat(flag, flag_part2_obf);
        strcat(flag, flag_part3_obf);
        strcat(flag, flag_part4_obf);
        strcat(flag, flag_part5_obf);
        printf("%s\n", flag);
    } else {
        printf("You must set the API key before logging in.\n");
    }
}

// Dummy Base64 decode function
char* base64_decode(const char* data, size_t input_length, size_t *output_length) {
    const char base64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    *output_length = input_length / 4 * 3;
    if (data[input_length - 1] == '=') (*output_length)--;
    if (data[input_length - 2] == '=') (*output_length)--;

    char *decoded_data = malloc(*output_length + 1);
    if (decoded_data == NULL) return NULL;

    for (int i = 0, j = 0; i < input_length;) {
        uint32_t sextet_a = data[i] == '=' ? 0 & i++ : strchr(base64_chars, data[i++]) - base64_chars;
        uint32_t sextet_b = data[i] == '=' ? 0 & i++ : strchr(base64_chars, data[i++]) - base64_chars;
        uint32_t sextet_c = data[i] == '=' ? 0 & i++ : strchr(base64_chars, data[i++]) - base64_chars;
        uint32_t sextet_d = data[i] == '=' ? 0 & i++ : strchr(base64_chars, data[i++]) - base64_chars;

        uint32_t triple = (sextet_a << 3 * 6) + (sextet_b << 2 * 6) + (sextet_c << 1 * 6) + (sextet_d << 0 * 6);

        if (j < *output_length) decoded_data[j++] = (triple >> 2 * 8) & 0xFF;
        if (j < *output_length) decoded_data[j++] = (triple >> 1 * 8) & 0xFF;
        if (j < *output_length) decoded_data[j++] = (triple >> 0 * 8) & 0xFF;
    }

    decoded_data[*output_length] = '\0';
    return decoded_data;
}

void reverse_string(char *str) {
    int len = strlen(str);
    for (int i = 0; i < len / 2; i++) {
        char temp = str[i];
        str[i] = str[len - i - 1];
        str[len - i - 1] = temp;
    }
}

void xor_decrypt(char *input, const char *key) {
    int input_len = strlen(input);
    int key_len = strlen(key);
    for (int i = 0; i < input_len; i++) {
        input[i] = input[i] ^ key[i % key_len];
    }
}