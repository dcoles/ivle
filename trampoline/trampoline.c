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
#include <syslog.h>
#include <sys/mount.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <limits.h>
#include <signal.h>

/* conf.h is admin-configured by the setup process.
 * It defines jail_base.
 */
#include "conf.h"

#include "norm.h"

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

/* Turn the process into a daemon using the standard
 * 2-fork technique.
 */
void daemonize(void)
{
    pid_t pid, sid;

    /* already a daemon */
    if ( getppid() == 1 ) return;

    /* Fork off the parent process */
    pid = fork();
    if (pid < 0) {
        exit(1);
    }
    /* If we got a good PID, then we can exit the parent process. */
    if (pid > 0) {
        exit(0);
    }

    /* At this point we are executing as the child process */

    /* Change the file mode mask */
    umask(022);

    /* Create a new SID for the child process */
    sid = setsid();
    if (sid < 0) {
        exit(1);
    }

    /* Change the current working directory.  This prevents the current
       directory from being locked; hence not being able to remove it. */
    if ((chdir("/")) < 0) {
        exit(1);
    }

    /* Redirect standard files to /dev/null */
    freopen( "/dev/null", "r", stdin);
    freopen( "/dev/null", "w", stdout);
    freopen( "/dev/null", "w", stderr);
}

static void usage(const char* nm)
{
    fprintf(stderr,
        "usage: %s [-d] [-u] <uid> <jail> <cwd> <program> [args...]\n", nm);
    exit(1);
}

#ifdef IVLE_AUFS_JAILS
/* Die more pleasantly if mallocs fail. */
void *die_if_null(void *ptr)
{
    if (ptr == NULL)
    {
        perror("not enough memory");
        exit(1);
    }
    return ptr;
}

/* Find the path of the user components of a jail, given a mountpoint. */
char *jail_src(const char* jailpath)
{
    char* src;
    int srclen;
    int dstlen;

    srclen = strlen(jail_src_base);
    dstlen = strlen(jail_base);
    
    src = die_if_null(malloc(strlen(jailpath) + (srclen - dstlen) + 1));
    strcpy(src, jail_src_base);
    strcat(src, jailpath+dstlen);

    return src;
}

/* Check for the validity of a jail in the given path, mounting it if it looks
 * empty.
 * TODO: Updating /etc/mtab would be nice. */
void mount_if_needed(const char* jailpath)
{
    char *jailsrc;
    char *jaillib;
    char *mountdata;

    /* Check if there is something useful in the jail. If not, it's probably
     * not mounted. */
    jaillib = die_if_null(malloc(strlen(jailpath) + 5));
    sprintf(jaillib, "%s/lib", jailpath);

    if (access(jaillib, F_OK))
    {
        /* No /lib? Mustn't be mounted. Mount it, creating the dir if needed. */
        if (access(jailpath, F_OK))
        {
             if(mkdir(jailpath, 0755))
             {
                 syslog(LOG_ERR, "could not create mountpoint %s\n", jailpath);
                 perror("could not create jail mountpoint");
                 exit(1);
             }
             syslog(LOG_NOTICE, "created mountpoint %s\n", jailpath);
        }
       
        jailsrc = jail_src(jailpath);
        mountdata = die_if_null(malloc(3 + strlen(jailsrc) + 4 + strlen(jail_system) + 3 + 1));
        sprintf(mountdata, "br:%s=rw:%s=ro", jailsrc, jail_system);
        if (mount("none", jailpath, "aufs", 0, mountdata))
        {
            syslog(LOG_ERR, "could not mount %s\n", jailpath);
            perror("could not mount");
            exit(1);
        } 

        syslog(LOG_INFO, "mounted %s\n", jailpath);

        free(jailsrc);
        free(mountdata);
    }

    free(jaillib);
}
#endif /* IVLE_AUFS_JAILS */

/* Unsets any signal mask applied by the parent process */
void unmask_signals()
{
    sigset_t* sigset;
    sigset = die_if_null(malloc(sizeof(sigset_t)));
    sigemptyset(sigset);
    sigprocmask(SIG_SETMASK, sigset, NULL);
    free(sigset);
}

int main(int argc, char* const argv[])
{
    char* jailpath;
    char* work_dir;
    char* prog;
    char* const * args;
    int uid;
    int arg_num = 1;
    int daemon_mode = 0;
    int unlimited = 0;
    char canonical_jailpath[PATH_MAX];

    /* Disallow execution from all users but the whitelisted ones, and root */
    if (!uid_allowed(getuid()))
    {
        fprintf(stderr, "only the web server may execute trampoline\n");
        exit(1);
    }

    /* Args check and usage */
    if (argc < 5)
    {
        usage(argv[0]);
    }

    if (strcmp(argv[arg_num], "-d") == 0)
    {
        if (argc < 6)
        {
            usage(argv[0]);
        }
        daemon_mode = 1;
        arg_num++;
    }

    unmask_signals();

    if (strcmp(argv[arg_num], "-u") == 0)
    {
        if (argc < 6)
        {
            usage(argv[0]);
        }
        unlimited = 1;
        arg_num++;
    }
    uid = atoi(argv[arg_num++]);
    jailpath = argv[arg_num++];
    work_dir = argv[arg_num++];
    prog = argv[arg_num];
    args = argv + arg_num;

    /* Disallow suiding to the root user */
    if (uid == 0)
    {
        fprintf(stderr, "cannot set up a jail as root\n");
        exit(1);
    }

    /* Jail path must be an absolute path,
     * and it must begin with jail_base.
     */
    if (norm(canonical_jailpath, PATH_MAX, jailpath) != 0)
    {
        fprintf(stderr, "bad jail path: %s\n", jailpath);
        exit(1);
    }
    if (strncmp(canonical_jailpath, jail_base, strlen(jail_base)))
    {
        fprintf(stderr, "bad jail path: %s\n", jailpath);
        exit(1);
    }

    openlog("trampoline", LOG_CONS | LOG_PID | LOG_NDELAY, LOG_USER);

    #ifdef IVLE_AUFS_JAILS
    mount_if_needed(canonical_jailpath);
    #endif /* IVLE_AUFS_JAILS */

    /* chroot into the jail.
     * Henceforth this process, and its children, cannot see anything above
     * canoncial_jailpath. */
    if (chroot(canonical_jailpath))
    {
        syslog(LOG_ERR, "chroot to %s failed\n", canonical_jailpath);

        perror("could not chroot");
        exit(1);
    }

    /* chdir into the specified working directory */
    if (chdir(work_dir))
    {
        perror("could not chdir");
        exit(1);
    }

    /* setuid to the given user ID.
     * Henceforth we will be running as this user instead of root.
     */
    if (setgid(uid))
    {
        perror("could not setgid");
        exit(1);
    }

    if (setuid(uid))
    {
        perror("could not setuid");
        exit(1);
    }

    if (daemon_mode)
    {
        daemonize();
    }

    /* set user resource limits */
    if (!unlimited)
    {
        struct rlimit l;
        /* Process data segment in memory */
        l.rlim_cur = 192 * 1024 * 1024; /* 192MiB */
        l.rlim_max = 256 * 1024 * 1024; /* 256MiB */
        if (setrlimit(RLIMIT_AS, &l))
        {
            perror("could not setrlimit/RLIMIT_AS");
            exit(1);
        }

        /* Core */
        l.rlim_cur = 0;
        l.rlim_max = 0;
        if (setrlimit(RLIMIT_CORE, &l))
        {
            perror("could not setrlimit/RLIMIT_CORE");
            exit(1);
        }

        /* CPU */
        l.rlim_cur = 25;
        l.rlim_max = 30;
        if (setrlimit(RLIMIT_CPU, &l))
        {
            perror("could not setrlimit/RLIMIT_CPU");
            exit(1);
        }

        /* File Size */
        l.rlim_cur = 64 * 1024 * 1024; /* 64Mb */
        l.rlim_max = 72 * 1024 * 1024; /* 72Mb */
        if (setrlimit(RLIMIT_FSIZE, &l))
        {
            perror("could not setrlimit/RLIMIT_FSIZE");
            exit(1);
        }
    }

    /* exec (replace this process with the a new instance of the target
     * program). Pass along all the arguments.
     * Note that for script execution, the "program" will be the interpreter,
     * and the first argument will be the script. */
    execv(prog, args);

    /* nb exec won't return unless there was an error */
    syslog(LOG_ERR, "exec of %s in %s failed", prog, canonical_jailpath);

    perror("could not exec");
    closelog();
    return 1;
}
