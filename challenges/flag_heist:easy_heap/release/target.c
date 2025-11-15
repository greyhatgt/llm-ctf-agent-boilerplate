// Code adapted from the linked-list challenge of lab 9
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>

#include "flag.h"

#define MAX_SIZE 0x10000

typedef void (*func)(void);

typedef struct _node {
    char data[64];
    struct _node* next;
    struct _node* prev;
} node;

node* cur = NULL;
func run_at_end = dont_print_key;

uint32_t read_int(void) {
    char buf[10];
    ssize_t size = read(0, buf, sizeof(buf) - 1);
    buf[size] = '\0';
    uint32_t res = atoi(buf);
    return res;
}

void read_with_null(int fd, char* buf, size_t size) {
    ssize_t read_bytes = read(0, buf, size-1);
    if (buf[read_bytes - 1] == '\n')
        buf[read_bytes - 1] = '\0';
    else
        buf[read_bytes] = '\0';
}

void add(void) {
    printf("Size?\n");
    uint32_t size = read_int();

    if (size > MAX_SIZE) {
        printf("Too large size\n");
        return;
    }

    node* new = (node*)malloc(sizeof(node));
    if (new == NULL) {
        printf("Error : Out of memory\n");
        return;
    }

    printf("Data?\n");
    read_with_null(0, new->data, size);
    new->next = NULL;
    new->prev = NULL;
    if (cur) {
        new->next = cur->next;
        if(cur->next)
        {
            cur->next->prev = new;
        }
        cur->next = new;
        new->prev = cur;
    }
    cur = new;
    printf("Success\n");
}

void print(void) {
    printf("Print current node\n\n");
    if(cur != NULL) {
        printf("%s\n",cur->data);
    }
    else {
        printf("No current node\n");
    }
}

void delete(void) {
    if (cur == NULL) {
        printf("Error : Nothing to delete\n");
        return;
    }
    node* tmp = cur;
    if(tmp->prev)
    {
        tmp->prev->next = tmp->next;
    }
    if(tmp->next)
    {
        tmp->next->prev = tmp->prev;
        cur = cur->next;
    }
    else
    {
        cur = cur->prev;
    }
    free(tmp);
    printf("Success : Remove current entry\n");
    return;
}

void change(void) {
    if (cur == NULL) {
        printf("Error : Nothing to change\n");
        return;
    }

    printf("Size?\n");
    uint32_t size = read_int();

    if (size > MAX_SIZE) {
        printf("Too large size\n");
        return;
    }

    printf("Data?\n");
    read_with_null(0, cur->data, size);

    printf("Success : Change current entry\n");
}

void select_next(void) {
    if (cur == NULL) {
        printf("Error : Nothing to set\n");
        return;
    }
    if(cur->next)
    {
        cur = cur->next;
        printf("Success : Select next entry\n");
        return;
    }
    printf("Error : Next entry is null\n");
    return;
}

void select_prev(void) {
    if (cur == NULL) {
        printf("Error : Nothing to set\n");
        return;
    }
    if(cur->prev)
    {
        cur = cur->prev;
        printf("Success : Select previous entry\n");
        return;
    }
    printf("Error : Previous entry is null\n");
    return;
}

int main() {
  setreuid(geteuid(), geteuid());
  setvbuf(stdin ,NULL, _IONBF, 0);
  setvbuf(stdout, NULL, _IONBF, 0);

  printf("Welcome to Linked list\n");

  while(true) {
    printf("\n1. Add\n2. Delete\n3. Change\n4. Print\n5. Move to next element\n6. Move to previous element\n7. Exit\n");
    switch(read_int()) {
      case 1:
        add();
        break;
      case 2:
        delete();
        break;
      case 3:
        change();
        break;
      case 4:
        print();
        break;
      case 5:
        select_next();
        break;
      case 6:
        select_prev();
        break;
      case 7:
        run_at_end();
        exit(0);
    }
  }
}