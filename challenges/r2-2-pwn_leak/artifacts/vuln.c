#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void win() {
    FILE *f = fopen("challenges/r2-2-pwn_leak/artifacts/flag", "r");
    if (!f) {
        puts("Flag missing.");
        return;
    }
    char buf[256];
    if (fgets(buf, sizeof(buf), f)) {
        size_t n = strlen(buf);
        if (n && buf[n-1] == '\n') buf[n-1] = '\0';
        printf("Nice! Flag: %s\n", buf);
    }
    fclose(f);
    exit(0);
}

void vuln() {
    char buf[128];
    puts("Send something:");
    // intentionally vulnerable
    gets(buf);
    puts("Done.");
}

int main() {
    setbuf(stdout, NULL);
    setbuf(stdin, NULL);
    // explicit leak printed at startup
    printf("[info] win() is at %p\n", (void*)win);
    puts("Welcome to LeakPwn!");
    vuln();
    puts("Bye");
    return 0;
}
