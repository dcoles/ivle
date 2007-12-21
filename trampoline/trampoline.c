/* IVLE - Informatics Virtual Learning Environment
 * Copyright (C) 2007-2008 The University of Melbourne
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * Program: Trampoline
 * Author:  Tom Conway, Matt Giuca
 * Date:    20/12/2007
 *
 * This program runs a given program in a given working dir.
 * First, it chroots to a jail path and setuids to a given user ID.
 * This is intented to provide a safe execution environment for arbitrary
 * programs and scripts.
 *
 * Scripts (such as Python programs) should be executed by supplying
 * "/usr/bin/python" as the program, and the script as the first argument.
 *
 * Usage: trampoline uid jail-path working-path program [args...]
 * Must run as root. Will safely setuid to the supplied uid, checking that it
 * is not root. Recommended that the file is set up as follows:
 *  sudo chown root:root trampoline; sudo chroot +s trampoline
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* conf.h is admin-configured by the setup process.
 * It defines jail_base.
 */
#include "conf.h"

/* Argument names */
#define ARG_UID         1
#define ARG_JAILPATH    2
#define ARG_CWD         3
#define ARG_PROG        4

#define MIN_ARGC        5

#define UID_ROOT        0

/* Returns TRUE if the given uid is allowed to execute trampoline.
 * Only root or the web server should be allowed to execute.
 * This is determined by the whitelist allowed_uids in conf.h.
 */
int uid_allowed(int uid)
{
    int i;
    /* root is always allowed to execute trampoline */
    if (uid == 0)
        return 1;
    /* loop over all allowed_uids */
    for (i=(sizeof(allowed_uids)/sizeof(*allowed_uids))-1; i>=0; i--)
    {
        if (allowed_uids[i] == uid)
            return 1;
    }
    /* default to disallowing */
    return 0;
}

int main(int argc, char* const argv[])
{
    char* jailpath;
    int uid;

    /* Disallow execution from all users but the whitelisted ones, and root */
    if (!uid_allowed(getuid()))
    {
        fprintf(stderr, "only the web server may execute trampoline\n");
        exit(1);
    }

    /* Args check and usage */
    if (argc < MIN_ARGC)
    {
        fprintf(stderr, "usage: %s <uid> <jail> <cwd> <program> [args...]\n",
            argv[0]);
        exit(EXIT_FAILURE);
    }

    /* Disallow suiding to the root user */
    uid = atoi(argv[ARG_UID]);
    if (uid == UID_ROOT)
    {
        fprintf(stderr, "cannot set up a jail as root\n");
        exit(1);
    }

    /* Jail path must:
     * Be non-empty
     * Start with a '/'
     * Not contain "/.."
     * Begin with jail_base
     */
    jailpath = argv[ARG_JAILPATH];
    if (strlen(jailpath) < 1 || jailpath[0] != '/'
            || strstr(jailpath, "/..")
            || strncmp(jailpath, jail_base, strlen(jail_base)))
    {
        fprintf(stderr, "bad jail path: %s\n", jailpath);
        exit(1);
    }

    /* chroot into the jail.
     * Henceforth this process, and its children, cannot see anything above
     * jailpath. */
    if (chroot(jailpath))
    {
        perror("could not chroot");
        exit(1);
    }

    /* chdir into the specified working directory */
    if (chdir(argv[ARG_CWD]))
    {
        perror("could not chdir");
        exit(1);
    }

    /* setuid to the given user ID.
     * Henceforth we will be running as this user instead of root.
     */
    if (setuid(uid))
    {
        perror("could not setuid");
        exit(1);
    }

    /* exec (replace this process with the a new instance of the target
     * program). Pass along all the arguments.
     * Note that for script execution, the "program" will be the interpreter,
     * and the first argument will be the script. */
    execv(argv[ARG_PROG], argv + ARG_PROG);

    /* nb exec won't return unless there was an error */
    perror("could not exec");
    return EXIT_FAILURE;
}
