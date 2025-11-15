#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <wchar.h>
#include <locale.h>

#define BUFSIZE 16
#define FLAGSIZE 64
#define INPSIZE 10

void win() {
  char buf[FLAGSIZE];
  char filler[BUFSIZE];
  FILE *f = fopen("flag","r");
  if (f == NULL) {
    printf("%s %s", "Please create 'flag.txt' in this directory with your",
                    "own debugging flag.\n");
    exit(0);
  }

  fgets(buf,FLAGSIZE,f); // size bound read
}

void UnderConstruction() {
        // this function is under construction
        char consideration[BUFSIZE];
        char *gtid, *gtemail, *homecountry, *major, *age, *idk;
	char *p,*q, *r;
        unsigned long *age1;
        unsigned long *age2;
        unsigned long *age3;
        unsigned long *age4;
        unsigned long *age5;
        unsigned long *age6;
        unsigned long *age7;        
        unsigned long *age8; 
        unsigned long *age9; 
	printf("User information : %p %p %p %p %p %p\n",gtid, gtemail, homecountry, major, age, idk);
	printf("Names of user: %p %p %p\n", p,q,r);
        printf("Age of user: %p %p %p %p %p %p %p %p %p\n",age1,age2,age3,age4,age5,age6,age7,age8,age9);
        fflush(stdout);
}

void vuln(){
   char buf[INPSIZE];
   printf("this file is under construction\n");
   gets(buf);
   printf("%s\n",buf);
   return;
}

int main(int argc, char **argv){

  setvbuf(stdout, NULL, _IONBF, 0);
  gid_t gid = getegid();
  setresgid(gid, gid, gid);
  vuln();
  printf("Bye!");
  return 0;
}

