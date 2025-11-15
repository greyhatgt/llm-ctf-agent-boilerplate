#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>
#include <string.h>
#include <err.h>

////////////////////////////////// Array of Steps
// Right Arrow steps
int right_arrow_steps[] = {
    1, 10, 12, 14, 15, 16, 18, 24, 26, 28, 29, 30, 36, 38, 44, 46, 48, 49, 50, 
    52, 62, 74, 77, 79, 80, 81, 87, 88, 97, 99, 102, 110, 111, 112, 117, 120, 
    121, 124, 126, 129, 136, 137, 138, 143
};

// Left Arrow steps
int left_arrow_steps[] = {
    2, 11, 17, 19, 21, 22, 23, 25, 35, 37, 39, 41, 42, 43, 45, 51, 53, 55, 56, 
    57, 63, 70, 72, 75, 83, 84, 85, 90, 93, 94, 101, 104, 106, 107, 108, 114, 
    115, 128, 131, 133, 134, 140, 141, 147
};

// Up Arrow steps
int up_arrow_steps[] = {
    4, 6, 7, 32, 34, 58, 60, 73, 86, 91, 98, 105, 113, 118, 122, 125, 132, 
    135, 142
};

// Down Arrow steps
int down_arrow_steps[] = {
    3, 5, 8, 9, 31, 33, 59, 61, 71, 78, 82, 89, 95, 100, 109, 116, 127, 139, 
    144, 148
};

// Left and Right steps
int left_and_right_steps[] = {
    31, 33, 64, 65, 68, 69, 76, 96, 103, 123, 130, 145, 146
};

// Down and Up steps
int down_and_up_steps[] = {
    13, 20, 27, 40, 47, 54, 66, 67, 92, 119
};


////////////// Sizes of the array 
int right_arrow_steps_size = sizeof(right_arrow_steps) / sizeof(right_arrow_steps[0]);
int left_arrow_steps_size = sizeof(left_arrow_steps) / sizeof(left_arrow_steps[0]);
int up_arrow_steps_size = sizeof(up_arrow_steps) / sizeof(up_arrow_steps[0]);
int down_arrow_steps_size = sizeof(down_arrow_steps) / sizeof(down_arrow_steps[0]);
int left_and_right_steps_size = sizeof(left_and_right_steps) / sizeof(left_and_right_steps[0]);
int down_and_up_steps_size = sizeof(down_and_up_steps) / sizeof(down_and_up_steps[0]);


// Steps
int step = 1;


// Function to simulate "pop all" by popping values from the stack into registers
void pop_all() {
    __asm__(
        "pop %edi;"   // Pop into edi
        "pop %esi;"   // Pop into esi
        "pop %ebp;"   // Pop into ebp
        "pop %ebx;"   // Pop into ebx
        "pop %edx;"   // Pop into edx
        "pop %ecx;"   // Pop into ecx
        "pop %eax;"   // Pop into eax
        "ret;"        // Return to the next address on the stack
    );
}


// Function to check if a given step is in the specified array
bool is_in_array(int step, int arr[], int size) {
    for (int i = 0; i < size; i++) {
        if (arr[i] == step) {
            return true;
        }
    }
    return false;
}



void vulnerable() {
    char buffer[64];
    printf("Enter your Steps of the YMCA Song:\n");
    read(STDIN_FILENO, buffer, 1000); 
}



//Help you get the right steps 
void direction(int num){
	if(num == 0 && is_in_array(step, right_arrow_steps, right_arrow_steps_size)) step++;
	if(num == 1 && is_in_array(step, left_arrow_steps, left_arrow_steps_size)) step++;
	if(num == 2 && is_in_array(step, up_arrow_steps, up_arrow_steps_size)) step++;
	if(num == 3 && is_in_array(step, down_arrow_steps, down_arrow_steps_size)) step++;
	if(num == 4 && is_in_array(step, left_and_right_steps, left_and_right_steps_size)) step++;
	if(num == 5 && is_in_array(step, down_and_up_steps, down_and_up_steps_size)) step++;
	printf("Current step value: %d\n", step);
	vulnerable();
}


void win() {
	printf("Final step value in win(): %d\n", step);
    if (step == 148) {
        printf("Congratulations! You have successfully crafted the ROP chain!\n");

        // Open and read the flag file
        // Use the absolute path in your popen call
	FILE *fp = fopen("flag", "r");
        if (fp == NULL) {
            perror("Failed to open flag file");
            exit(1);
        }

        // Read and print the contents of the flag file
        char flag[128];
        while (fgets(flag, sizeof(flag), fp) != NULL) {
            printf("%s", flag);
        }

        fclose(fp);
        exit(0);
    } else {
        printf("ROP chain incomplete or incorrect.\n");
        exit(1);
    }
}



int main(int argc, char **argv) {
  setreuid(geteuid(), geteuid());
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stdin, NULL, _IONBF, 0);
  printf("Welcome to ROP ROP Revolution!\n");
   vulnerable();  
   return 0;
}


