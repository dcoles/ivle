/* IVLE - Informatics Virtual Learning Environment
 * Copyright (C) 2008 The University of Melbourne
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
 * Program: Timount
 * Author:  William Grant
 * Date:    05/07/2008
 *
 * Timount ('timeout mounts') cleans up mounts after a period of inactivity.
 * It looks in the given directory of mountpoints, and attempts to unmount each
 * with the MNT_EXPIRE flag. This flag is reset whenever a process accesses
 * the mountpoint, meaning that a mountpoint will be unmounted only if it is
 * inactive for the interval between two timount invocations.
 *
 * It is unclear how frequently timount should optimally be run. Empirical data
 * specific to the installation will likely be required.
 *
 * Usage: timount <path>
 * Must run as root, and probably from cron.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <dirent.h>
#include <syslog.h>
#include <sys/mount.h>

#ifndef MNT_EXPIRE
/* For some reason this isn't defined in libc at the moment. */
#define MNT_EXPIRE 4
#endif

void usage(const char *prog)
{
    fprintf(stderr, "usage: %s <path>\n", prog);
    exit(1);
}

int main(int argc, const char *argv[])
{
    DIR *rootdir;
    struct dirent *mp;
    char *dirname;

    if (argc != 2)
        usage(argv[0]);

    openlog("timount", LOG_CONS | LOG_PID, LOG_USER);

    rootdir = opendir(argv[1]);

    while ((mp = readdir(rootdir)))
    {
        dirname = malloc(strlen(argv[1]) + strlen(mp->d_name) + 2);
        sprintf(dirname, "%s/%s", argv[1], mp->d_name);
        if (mp->d_name[0] != '.' && mp->d_name[0] != '_')
        {
            if (umount2(dirname, MNT_EXPIRE))
            {
                /* We failed to unmount, but did it set the expire flag? */
                if (errno == EAGAIN)
                    syslog(LOG_INFO, "marked %s for expiry\n", mp->d_name);
            }
            else
            {
                syslog(LOG_INFO, "unmounted %s\n", mp->d_name);
            }
        }
        free(dirname);
    }

    closedir(rootdir);
    closelog();
    return 0;
}
