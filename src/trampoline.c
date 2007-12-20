#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "conf.h"

int main(int argc, char* const argv[])
{
    if (argc < 6)
    {
        fprintf(stderr, "usage: %s <uid> <jail> <cwd> <interp> <script> [args...]\n", argv[0]);
        exit(1);
    }

    if (strlen(argv[2]) < 1 || argv[2][0] != '/'
            || strstr(argv[2], "/..")
            || strncmp(argv[2], jail_base, strlen(jail_base)))
    {
        fprintf(stderr, "bad path: %s\n", argv[2]);
        exit(1);
    }

    if (chroot(argv[2]))
    {
        perror("could not chroot");
        exit(1);
    }

    if (chdir(argv[3]))
    {
        perror("could not chdir");
        exit(1);
    }

    if (setuid(atoi(argv[1])))
    {
        perror("could not setuid");
        exit(1);
    }

    execv(argv[4], argv + 5);

    /* nb exec won't return unless there was an error */
    perror("could not exec");
    exit(1);
}
