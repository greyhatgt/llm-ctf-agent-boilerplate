#include <stdio.h>
#include <string.h>

int main(void) {
    char input[128];
    const char *password = "correcthorsebatterystaple";
    const char *flag = "flag{naive_plaintext_14232983}";

    printf("Enter password: ");
    if (!fgets(input, sizeof(input), stdin)) return 1;

    // strip newline
    size_t len = strlen(input);
    if (len && input[len-1] == '\n') input[len-1] = '\0';

    if (strcmp(input, password) == 0) {
        printf("Access granted! Flag: %s\n", flag);
        return 0;
    } else {
        printf("Access denied.\n");
        return 1;
    }
}
