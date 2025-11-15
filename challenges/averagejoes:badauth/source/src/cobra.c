#include <err.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "flag.h"
void checkPassword(char *password) {
  unsigned char temp[16];
  int fd = open("/dev/urandom", O_RDONLY);
  if (fd == -1)
    err(1, "Failed to open /dev/urandom");

  ssize_t result = read(fd, temp, 15);
  if (result != 15)
    err(1, "Failed to read from /dev/urandom");

  for (int i = 0; i < 16; i++) {
    if (temp[i] == '\0')
      break;
    password[i] = temp[i] % 94 + 33;
  }
  password[15] = '\0';
  close(fd);
}

int main(int argc, char *argv[]) {
  setreuid(geteuid(), geteuid());
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stdin, NULL, _IONBF, 0);

  char buf[100];
  while (true) {
    printf("Purple Cobra Training Facility\n(passwords change frequently!)\n");
    printf("Password: ");

    fgets(buf, sizeof(buf), stdin);
    char serverPassword[16] = {};
    checkPassword(serverPassword);

    if (!strcmp(buf, serverPassword)) {
      printf("Password OK :)\n");
      print_key("flag");
      return 0;

    } else {
      printf("Password Incorrect :(\n\n");
    }
  }
}
