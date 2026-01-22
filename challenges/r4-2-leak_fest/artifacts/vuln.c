/* vuln.c
 * Combined fmt-string leak + buffer overflow ret2libc challenge
 *
 * Compile with:
 *   gcc -no-pie -fno-stack-protector -O0 -g -o vuln vuln.c
 *
 * Described exploit:
 * - The 'leak_me' function reads a line and passes it directly to printf -> format string leak.
 *   Use that to leak puts@GOT (or other libc pointer).
 * - Then 'vuln' uses gets() into a small buffer. Overflow the saved return to call system(cmd)
 *   where 'cmd' is a static string in the binary pointing at the flag file path.
 *
 * Notes:
 * - No PIE (addresses static), NX is default (so must use ret2libc).
 * - Partial RELRO (GOT writable) not required for this chain; we use an infoleak + ret2libc.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>


void win() {
    FILE *f = fopen("challenges/r4-2-leak_fest/source/flag.txt", "r");
    if (!f) {
        puts("[*] reached win()");
        puts("Flag missing or cannot open file.");
        exit(1);
    }

    char buf[256];
    if (fgets(buf, sizeof(buf), f)) {
        /* strip trailing newline */
        size_t n = strlen(buf);
        if (n && buf[n-1] == '\n') buf[n-1] = '\0';
        printf("Nice! Flag: %s\n", buf);
    } else {
        puts("Flag file empty or read error.");
    }
    fclose(f);
    exit(0);
}

void leak_me() {
    char buf[256];
    puts("Send format string to leak addresses:");
    if (!fgets(buf, sizeof(buf), stdin)) return;
    /* deliberate format-string vulnerability */
    printf(buf);
    puts(""); /* newline sentinel */
}

void vuln() {
    char small[64];
    puts("Now overflow time: send payload:");
    /* intentionally unsafe */
    gets(small);
    puts("Thanks.");
}

int main() {
    /* predictable buffering */
    setbuf(stdout, NULL);
    setbuf(stdin, NULL);
    puts("[info] Welcome to fmt+ret2libc challenge.");
    printf("[info] puts() resolved at %p\n", (void*)puts);
    leak_me();
    vuln();
    puts("Bye.");
    return 0;
}
