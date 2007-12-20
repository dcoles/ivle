#!/usr/bin/env python
# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2008 The University of Melbourne
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# Module: setup
# Author: Matt Giuca
# Date:   12/12/2007

# This is a command-line application, for use by the administrator.
# This program configures, builds and installs IVLE in three separate steps.
# It is called with at least one argument, which specifies which operation to
# take.

# setup.py conf [args]
# Configures IVLE with machine-specific details, most notably, various paths.
# Either prompts the administrator for these details or accepts them as
# command-line args.
# Creates www/conf/conf.py and trampoline/conf.h.

# setup.py build
# Compiles all files and sets up a jail template in the source directory.
# Details:
# Compiles (GCC) trampoline/trampoline.c to trampoline/trampoline.
# Creates jail/.
# Creates standard subdirs inside the jail, eg bin, opt, home, tmp.
# Copies console/ to a location within the jail.
# Copies OS programs and files to corresponding locations within the jail
#   (eg. python and Python libs, ld.so, etc).
# Generates .pyc files for all the IVLE .py files.

# setup.py listmake (for developer use only)
# Recurses through the source tree and builds a list of all files which should
# be copied upon installation. This should be run by the developer before
# cutting a distribution, and the listfile it generates should be included in
# the distribution, avoiding the administrator having to run it.

# setup.py install [--nojail] [--dry|n]
# (Requires root)
# Create target install directory ($target).
# Create $target/bin.
# Copy trampoline/trampoline to $target/bin.
# chown and chmod the installed trampoline.
# Copy www/ to $target.
# Copy jail/ to jails template directory (unless --nojail specified).

# TODO: List in help, and handle, args for the conf operation

import os
import sys
import getopt
import string
import errno

# Main function skeleton from Guido van Rossum
# http://www.artima.com/weblogs/viewpost.jsp?thread=4829

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Print the opening spiel including the GPL notice

    print """IVLE - Informatics Virtual Learning Environment Setup
Copyright (C) 2007-2008 The University of Melbourne
IVLE comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions. See LICENSE.txt for details.

IVLE Setup
"""

    # First argument is the name of the setup operation
    try:
        operation = argv[1]
    except IndexError:
        # Print usage message and exit
        help([])
        return 1

    # Call the requested operation's function
    try:
        return {
            'help' : help,
            'conf' : conf,
            'build' : build,
            'listmake' : listmake,
            'install' : install,
        }[operation](argv[2:])
    except KeyError:
        print >>sys.stderr, (
            """Invalid operation '%s'. Try python setup.py help."""
            % operation)

    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
        except getopt.error, msg:
            raise Usage(msg)
        # more code, unchanged
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

# Operation functions

def help(args):
    if args == []:
        print """Usage: python setup.py operation [args]
Operation (and args) can be:
    help [operation]
    conf [args]
    build
    install [--nojail] [-n|--dry]
"""
        return 1
    elif len(args) != 1:
        print """Usage: python setup.py help [operation]"""
        return 2
    else:
        operation = args[0]

    if operation == 'help':
        print """python setup.py help [operation]
Prints the usage message or detailed help on an operation, then exits."""
    elif operation == 'conf':
        print """python setup.py conf [args]
Configures IVLE with machine-specific details, most notably, various paths.
Either prompts the administrator for these details or accepts them as
command-line args.
Creates www/conf/conf.py and trampoline/conf.h.
Args are:
"""
    elif operation == 'build':
        print """python setup.py build
Compiles all files and sets up a jail template in the source directory.
Details:
Compiles (GCC) trampoline/trampoline.c to trampoline/trampoline.
Creates jail/.
Creates standard subdirs inside the jail, eg bin, opt, home, tmp.
Copies console/ to a location within the jail.
Copies OS programs and files to corresponding locations within the jail
  (eg. python and Python libs, ld.so, etc).
Generates .pyc files for all the IVLE .py files."""
    elif operation == 'listmake':
        print """python setup.py listmake
(For developer use only)
Recurses through the source tree and builds a list of all files which should
be copied upon installation. This should be run by the developer before
cutting a distribution, and the listfile it generates should be included in
the distribution, avoiding the administrator having to run it."""
    elif operation == 'install':
        print """sudo python setup.py install [--nojail] [--dry|-n]
(Requires root)
Create target install directory ($target).
Create $target/bin.
Copy trampoline/trampoline to $target/bin.
chown and chmod the installed trampoline.
Copy www/ to $target.
Copy jail/ to jails template directory (unless --nojail specified).

--nojail    Do not copy the jail.
--dry | -n  Print out the actions but don't do anything."""
    else:
        print >>sys.stderr, (
            """Invalid operation '%s'. Try python setup.py help."""
            % operation)
    return 1

def conf(args):
    # Set up some variables

    cwd = os.getcwd()
    # the files that will be created/overwritten
    conffile = os.path.join(cwd, "www/conf/conf.py")
    conf_hfile = os.path.join(cwd, "trampoline/conf.h")

    # Fixed config options that we don't ask the admin

    default_app = "dummy"

    print """This tool will create the following files:
    %s
    %s
prompting you for details about your configuration. The file will be
overwritten if it already exists. It will *not* install or deploy IVLE.

Please hit Ctrl+C now if you do not wish to do this.
""" % (conffile, conf_hfile)

    # Get information from the administrator
    # If EOF is encountered at any time during the questioning, just exit
    # silently

    root_dir = query_user(
    """Root directory where IVLE is located (in URL space):
    (eg. "/" or "/ivle")""")
    ivle_install_dir = query_user(
    'Root directory where IVLE is located (on the local file system):\n'
    '(eg. "/home/informatics/ivle")')
    jail_base = query_user(
    """Root directory where user files are stored (on the local file system):
    (eg. "/home/informatics/jails")""")

    # Write www/conf/conf.py

    try:
        conf = open(conffile, "w")

        conf.write("""# IVLE Configuration File
# conf.py
# Miscellaneous application settings


# In URL space, where in the site is IVLE located. (All URLs will be prefixed
# with this).
# eg. "/" or "/ivle".
root_dir = "%s"

# In the local file system, where IVLE is actually installed.
# This directory should contain the "www" and "bin" directories.
ivle_install_dir = "%s"

# In the local file system, where are the student/user file spaces located.
# The user jails are expected to be located immediately in subdirectories of
# this location.
jail_base = "%s"

# Which application to load by default (if the user navigates to the top level
# of the site). This is the app's URL name.
# Note that if this app requires authentication, the user will first be
# presented with the login screen.
default_app = "%s"
""" % (root_dir, ivle_install_dir, jail_base, default_app))
        
        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote www/conf/conf.py"

    # Write trampoline/conf.h

    try:
        conf = open(conf_hfile, "w")

        conf.write("""/* IVLE Configuration File
 * conf.h
 * Administrator settings required by trampoline.
 * Note: trampoline will have to be rebuilt in order for changes to this file
 * to take effect.
 */

/* In the local file system, where are the jails located.
 * The trampoline does not allow the creation of a jail anywhere besides
 * jail_base or a subdirectory of jail_base.
 */
static const char* jail_base = "%s";
""" % (jail_base))

        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote trampoline/conf.h"

    print
    print "You may modify the configuration at any time by editing"
    print conffile
    print conf_hfile
    print
    return 0

def build(args):
    dry = False     # Set to True later if --dry

    # Compile the trampoline
    action_runprog('gcc', ['-Wall', '-o', 'trampoline/trampoline',
        'trampoline/trampoline.c'], dry)

    # Create the jail and its subdirectories
    action_mkdir('jail')
    action_mkdir('jail/bin')
    action_mkdir('jail/lib')
    action_mkdir('jail/usr')
    action_mkdir('jail/usr/bin')
    action_mkdir('jail/usr/lib')
    action_mkdir('jail/opt')
    action_mkdir('jail/home')
    action_mkdir('jail/tmp')

    # TODO: Copy console into the jail
    # TODO: Copy operating system files into the jail
    # TODO: Compile .py files into .pyc files

    return 0

def listmake(args):
    print "Listmake"
    return 0

def install(args):
    print "Install"
    return 0

# The actions call Python os functions but print actions and handle dryness.
# May still throw os exceptions if errors occur.

def action_runprog(prog, args, dry):
    """Runs a unix program. Searches in $PATH. Synchronous (waits for the
    program to return). Runs in the current environment. First prints the
    action as a "bash" line.

    prog: String. Name of the program. (No path required, if in $PATH).
    args: [String]. Arguments to the program.
    dry: Bool. If True, prints but does not execute.
    """
    print prog, string.join(args, ' ')
    if not dry:
        os.spawnvp(os.P_WAIT, prog, args)

def action_mkdir(path):
    """Calls mkdir. Silently ignored if the directory already exists."""
    print "mkdir", path
    try:
        os.mkdir(path)
    except OSError, (err, msg):
        if err != errno.EEXIST:
            raise

def query_user(prompt):
    """Prompts the user for a string, which is read from a line of stdin.
    Exits silently if EOF is encountered. Returns the string, with spaces
    removed from the beginning and end.
    """
    sys.stdout.write(prompt)
    sys.stdout.write("\n>")
    try:
        val = sys.stdin.readline()
    except KeyboardInterrupt:
        # Ctrl+C
        sys.stdout.write("\n")
        sys.exit(1)
    sys.stdout.write("\n")
    if val == '': sys.exit(1)
    return val.strip()

if __name__ == "__main__":
    sys.exit(main())
