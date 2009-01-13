#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include "norm.h"

#define SKP()               \
    do {                    \
        s++;                \
    } while (0)

#define CPY()               \
    do {                    \
        *d++ = *s++;        \
    } while (0)

#define MRK()               \
    do {                    \
        PUSH();             \
    } while (0)

#define BKP()               \
    do {                    \
        POP();              \
    } while (0)

#define BKP2()              \
    do {                    \
        POP();              \
        POP();              \
    } while (0)

#define PUSH()              \
    do {                    \
        stk[top++] = d;     \
    } while (0)

#define POP()               \
    do {                    \
        if (top == 0)       \
        {                   \
            dest[0] = '\0'; \
            return -1;      \
        }                   \
        d = stk[--top];     \
    } while (0)

/*
 * Normalize the unix pathname in src eliminating . and .. sequences
 * to yield an absolute path. Returns 0 on success, and -1 on error.
 */
int norm(char* dest, int len, const char* src)
{
    const char* s = src;
    char* d = dest;
    char* stk[256];
    int top = 0;
    enum { L0, L1, L2, L3, L4 } state = L0;
    assert(strlen(src) <= len);

    while (*s)
    {
        char c = *s;
        enum { slash, dot, other } cls;
        switch (c)
        {
            case '/':
            {
                cls = slash;
                break;
            }
            case '.':
            {
                cls = dot;
                break;
            }
            default:
            {
                cls = other;
            }
        }
        switch (state)
        {
            case L0:
            {
                switch (cls)
                {
                    case slash:
                    {
                        CPY();
                        state = L1;
                        break;
                    }
                    case dot:
                    case other:
                    {
                        dest[0] = '\0';
                        return -1;
                    }
                }
                break;
            }
            case L1:
            {
                switch (cls)
                {
                    case slash:
                    {
                        SKP();
                        break;
                    }
                    case dot:
                    {
                        MRK();
                        CPY();
                        state = L2;
                        break;
                    }
                    case other:
                    {
                        MRK();
                        CPY();
                        state = L4;
                        break;
                    }
                }
                break;
            }
            case L2:
            {
                switch (cls)
                {
                    case slash:
                    {
                        BKP();
                        state = L1;
                        break;
                    }
                    case dot:
                    {
                        CPY();
                        state = L3;
                        break;
                    }
                    case other:
                    {
                        CPY();
                        state = L4;
                        break;
                    }
                }
                break;
            }
            case L3:
            {
                switch (cls)
                {
                    case slash:
                    {
                        BKP2();
                        state = L1;
                        break;
                    }
                    case dot:
                    case other:
                    {
                        CPY();
                        state = L4;
                        break;
                    }
                }
                break;
            }
            case L4:
            {
                switch (cls)
                {
                    case slash:
                    {
                        CPY();
                        state = L1;
                        break;
                    }
                    case dot:
                    case other:
                    {
                        CPY();
                        break;
                    }
                }
                break;
            }
        }
    }
    *d = '\0';
    return 0;
}
