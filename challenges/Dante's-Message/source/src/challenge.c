#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main() {
    setreuid(geteuid(), geteuid());
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    // Ciphertext string provided by you
    const char *ciphertext = "D'`%^p\\7<|:zzVw543?r0)(^&%[HiEDV|BccQ,v<)s[q7uWmlqpi/POkd*Kg`_^$bD`_^W{[ZY;Qu8NMLpPINGLEDh+GF?>=aA@\"8=6;4381U5.3,+*N.-,lk#G!&%|{z@~}_uzsxqpo5srkj0nmlkjibJ`&d]\\[Z~^@\\[ZSwQPUNMq43IHMLEih+GF?>=a;@?8\\I";
    
    // Print the ciphertext to stdout
    printf("%s\n", ciphertext);

    return 0;
}
