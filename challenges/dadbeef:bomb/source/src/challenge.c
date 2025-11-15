#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <err.h>
#include <stdint.h>
#include <time.h>

#include "flag.h"

char *password = "is it this one?";
char *temp = "it couldn't be";

void handle_failure_1(char *buf) {
  char msg[100];
  snprintf(msg, sizeof(msg), "Wrong! Oops, try again! You put %s\n", buf);
  printf(msg);
  exit(0);
}

void handle_failure_2() {
  char *msg = "No, sorry!\n";
  printf(msg);
  exit(0);
}

void handle_failure_3(char *buf) {
  char *msg = "Nope!\n";
  printf(msg);
  exit(0);
}

void final_stage() {
    //for now to get this to work changed flag.h but we can change it back
    //TODO: change flag in docker/flag? 

    //Was thinking to do a format string vulnerability to get to this final stage
    print_key("../../docker/flag");
    exit(0);
}

void stage_3() {
   char *buf = password;
   printf("[3] another password?\n");
   
   if (strcmp(buf, password)) {
       handle_failure_3(buf);
   }

   char t[12];
   srand(time(NULL));

   for (int xx = 0; xx < 12; ++xx) {
       t[xx] = (rand() ^ 17) + 10;
   }
   t[11] = '\0';

   char bufr[1024];
   fgets(bufr, sizeof(bufr), stdin);

   if (strcmp(bufr, t)) {
       handle_failure_3(bufr);
   } else {
       printf("you entered: ");
       printf(buf);
       printf("congrats! now how to get the flag?\n");
       exit(0);
   }


}

void stage_2() {
   char buf[10];
   uint8_t num = 1238975;

   printf("[2] A number?\n");
   fgets(buf, sizeof(buf), stdin);

   if (num == atoi(buf)) {
       printf("Nice. \n");
       stage_3();
   } else {
       handle_failure_2();
   }

}
char *tmp = "or this?\n";

int main(int argc, char *argv[])
{
  setreuid(geteuid(), geteuid());
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stdin, NULL, _IONBF, 0);

  char buf[100];
  printf("Welcome to the challenge! Answer carefully, or you will have to start over.\n");
  printf("[1] Password:");

  fgets(buf, sizeof(buf), stdin);

  if (!strcmp(buf, tmp)) {
    printf("Ok, next.\n");
    stage_2();
  } else {
    handle_failure_1(buf);
  }

  return 0;
}
