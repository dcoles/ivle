#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include "norm.h"

#if 0
struct stack_t
{
    const char** items;
    size_t capacity;
    size_t top;
};
typedef stack_t Stack;

Stack* new_stack()
{
    Stack* s = (Stack*) malloc(sizeof(Stack));
    if (!s)
    {
        fprintf(stderr, "new_stack: Memory allocation failure! (1)\n");
        exit(1);
    }
    s->items = (const char**) malloc(16 * sizeof(const char*));
    if (!s->items)
    {
        fprintf(stderr, "new_stack: Memory allocation failure! (2)\n");
        exit(1);
    }   
    s->capacity = 16;
    s->top = 0;
    return s;
}

void stack_push(Stack* s,const char* itm)
{
    if (s->top == s->capacity)
    {
        int c = s->capacity * 2;
        const char** itms = (const char**) malloc(c * sizeof(const char*));
        if (!itms)
        {
            fprintf(stderr, "stack_push: Memory allocation failure! (1)\n");
            exit(1);
        }
        memcpy(itms, s->items, s->capacity * sizeof(const char*));
        free(s->items);
        s->items = itms;
        s->capacity = c;
    }
    s->items[s->top++] = itm;
}

const char* stack_pop(Stack* s)
{
    if (s->top == 0)
    {
        fprintf(stderr, "stack_pop: underflow!\n");
        exit(1);
    }
    return s->items[--(s->top)];
}

void old_stack(Stack* s)
{
    free(s->items);
    free(s);
}
#endif 0


/*
 * Normalize the unix pathname in src eliminating .. sequences
 * to yield an absolute path. Returns 0 on success, and -1 on
 * error.
 */
int norm(char* dest, int len, const char* src)
{
    const char* s = src;
    int l = strlen(src);
    char* d = dest;
    assert(l <= len);

    if (!*s || (*d++ = *s++) != '/')
    {
        dest[0] = '\0';
        return -1;
    }
    while (*s)
    {
        const char* t;
        int l;
        t = s;
        while (*s && (*d++ = *s++) != '/') ;
        l = s - t - 1;
        if (1) {
            char x[128];
            printf("%d\n",l);
            strncpy(x,t,l);
            x[l] = 0;
            fprintf(stderr,"%s\n",x);
        }
        if (strncmp(t, "..", l) == 0)
        {
            fprintf(stderr,"backtracking...\n");
            d -= 4; /* /../ */
            while (d > dest && *--d != '/')
            {
                d--;
            }
            if (d < dest)
            {
                /* underflow: too many .. sequences */
                dest[0] = '\0';
                return -1;
            }
        }
    }
    *d = '\0';
    fprintf(stderr, "returning: '%s'\n", dest);
    return 0;
}
