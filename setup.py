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

# setup.py listmake (for developer use only)
# Recurses through the source tree and builds a list of all files which should
# be copied upon installation. This should be run by the developer before
# cutting a distribution, and the listfile it generates should be included in
# the distribution, avoiding the administrator having to run it.

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

# setup.py install [--nojail] [--dry|n]
# (Requires root)
# Create target install directory ($target).
# Create $target/bin.
# Copy trampoline/trampoline to $target/bin.
# chown and chmod the installed trampoline.
# Copy www/ to $target.
# Copy jail/ to jails template directory (unless --nojail specified).

import os
import stat
import shutil
import sys
import getopt
import string
import errno
import mimetypes
import compileall
import getopt

# Try importing existing conf, but if we can't just set up defaults
# The reason for this is that these settings are used by other phases
# of setup besides conf, so we need to know them.
# Also this allows you to hit Return to accept the existing value.
try:
    confmodule = __import__("www/conf/conf")
    root_dir = confmodule.root_dir
    ivle_install_dir = confmodule.ivle_install_dir
    jail_base = confmodule.jail_base
except ImportError:
    # Just set reasonable defaults
    root_dir = "/ivle"
    ivle_install_dir = "/opt/ivle"
    jail_base = "/home/informatics/jails"
# Always defaults
allowed_uids = "0"

# Try importing install_list, but don't fail if we can't, because listmake can
# function without it.
try:
    import install_list
except:
    pass

# Mime types which will automatically be placed in the list by listmake.
# Note that listmake is not intended to be run by the final user (the system
# administrator who installs this), so the developers can customize the list
# as necessary, and include it in the distribution.
listmake_mimetypes = ['text/x-python', 'text/html',
    'application/x-javascript', 'application/javascript',
    'text/css', 'image/png']

# Main function skeleton from Guido van Rossum
# http://www.artima.com/weblogs/viewpost.jsp?thread=4829

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
        oper_func = {
            'help' : help,
            'conf' : conf,
            'build' : build,
            'listmake' : listmake,
            'install' : install,
        }[operation]
    except KeyError:
        print >>sys.stderr, (
            """Invalid operation '%s'. Try python setup.py help."""
            % operation)
    return oper_func(argv[2:])

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
    elif operation == 'listmake':
        print """python setup.py listmake
(For developer use only)
Recurses through the source tree and builds a list of all files which should
be copied upon installation. This should be run by the developer before
cutting a distribution, and the listfile it generates should be included in
the distribution, avoiding the administrator having to run it."""
    elif operation == 'conf':
        print """python setup.py conf [args]
Configures IVLE with machine-specific details, most notably, various paths.
Either prompts the administrator for these details or accepts them as
command-line args. Will be interactive only if there are no arguments given.
Takes defaults from existing conf file if it exists.
Creates www/conf/conf.py and trampoline/conf.h.
Args are:
    --root_dir
    --ivle_install_dir
    --jail_base
    --allowed_uids
As explained in the interactive prompt or conf.py.
"""
    elif operation == 'build':
        print """python -O setup.py build [--dry|-n]
Compiles all files and sets up a jail template in the source directory.
-O is recommended to cause compilation to be optimised.
Details:
Compiles (GCC) trampoline/trampoline.c to trampoline/trampoline.
Creates jail/.
Creates standard subdirs inside the jail, eg bin, opt, home, tmp.
Copies console/ to a location within the jail.
Copies OS programs and files to corresponding locations within the jail
  (eg. python and Python libs, ld.so, etc).
Generates .pyc or .pyo files for all the IVLE .py files.

--dry | -n  Print out the actions but don't do anything."""
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

def listmake(args):
    # We build two separate lists, by walking www and console
    list_www = build_list_py_files('www')
    list_console = build_list_py_files('console')
    # Make sure that the files generated by conf are in the list
    # (since listmake is typically run before conf)
    if "www/conf/conf.py" not in list_www:
        list_www.append("www/conf/conf.py")
    # Make sure that console/python-console is in the list
    if "console/python-console" not in list_console:
        list_console.append("console/python-console")
    # Write these out to a file
    cwd = os.getcwd()
    # the files that will be created/overwritten
    listfile = os.path.join(cwd, "install_list.py")

    try:
        file = open(listfile, "w")

        file.write("""# IVLE Configuration File
# install_list.py
# Provides lists of all files to be installed by `setup.py install' from
# certain directories.
# Note that any files with the given filename plus 'c' or 'o' (that is,
# compiled .pyc or .pyo files) will be copied as well.

# List of all installable files in www directory.
list_www = """)
        writelist_pretty(file, list_www)
        file.write("""
# List of all installable files in console directory.
list_console = """)
        writelist_pretty(file, list_console)

        file.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote install_list.py"

    print
    print ("You may modify the set of installable files before cutting the "
            "distribution:")
    print listfile
    print

    return 0

def build_list_py_files(dir):
    """Builds a list of all py files found in a directory and its
    subdirectories. Returns this as a list of strings."""
    pylist = []
    for (dirpath, dirnames, filenames) in os.walk(dir):
        # Exclude directories beginning with a '.' (such as '.svn')
        filter_mutate(lambda x: x[0] != '.', dirnames)
        # All *.py files are added to the list
        pylist += [os.path.join(dirpath, item) for item in filenames
            if mimetypes.guess_type(item)[0] in listmake_mimetypes]
    return pylist

def writelist_pretty(file, list):
    """Writes a list one element per line, to a file."""
    if list == []:
        file.write("[]\n")
    else:
        file.write('[\n')
        for elem in list:
            file.write('    %s,\n' % repr(elem))
        file.write(']\n')

def conf(args):
    global root_dir, ivle_install_dir, jail_base, allowed_uids
    # Set up some variables

    cwd = os.getcwd()
    # the files that will be created/overwritten
    conffile = os.path.join(cwd, "www/conf/conf.py")
    conf_hfile = os.path.join(cwd, "trampoline/conf.h")

    # Fixed config options that we don't ask the admin
    default_app = "dummy"

    # Get command-line arguments to avoid asking questions.

    (opts, args) = getopt.gnu_getopt(args, "", ['root_dir=',
                    'ivle_install_dir=', 'jail_base=', 'allowed_uids='])

    if args != []:
        print >>sys.stderr, "Invalid arguments:", string.join(args, ' ')
        return 2

    if opts == []:
        # Interactive mode. Prompt the user for all the values.

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

        root_dir = query_user(root_dir,
        """Root directory where IVLE is located (in URL space):""")
        ivle_install_dir = query_user(ivle_install_dir,
        'Root directory where IVLE will be installed (on the local file '
        'system):')
        jail_base = query_user(jail_base,
        """Root directory where the jails (containing user files) are stored
(on the local file system):""")
        allowed_uids = query_user(allowed_uids,
        """UID of the web server process which will run IVLE.
Only this user may execute the trampoline. May specify multiple users as
a comma-separated list.
    (eg. "1002,78")""")

    else:
        opts = dict(opts)
        # Non-interactive mode. Parse the options.
        if '--root_dir' in opts:
            root_dir = opts['--root_dir']
        if '--ivle_install_dir' in opts:
            ivle_install_dir = opts['--ivle_install_dir']
        if '--jail_base' in opts:
            jail_base = opts['--jail_base']
        if '--allowed_uids' in opts:
            allowed_uids = opts['--allowed_uids']

    # Error handling on input values
    try:
        allowed_uids = map(int, allowed_uids.split(','))
    except ValueError:
        print >>sys.stderr, (
        "Invalid UID list (%s).\n"
        "Must be a comma-separated list of integers." % allowed_uids)
        return 1

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

/* Which user IDs are allowed to run the trampoline.
 * This list should be limited to the web server user.
 * (Note that root is an implicit member of this list).
 */
static const int allowed_uids[] = { %s };
""" % (jail_base, repr(allowed_uids)[1:-1]))

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
    action_mkdir('jail', dry)
    action_mkdir('jail/bin', dry)
    action_mkdir('jail/lib', dry)
    action_mkdir('jail/usr/bin', dry)
    action_mkdir('jail/usr/lib', dry)
    action_mkdir('jail/opt/ivle', dry)
    action_mkdir('jail/home', dry)
    action_mkdir('jail/tmp', dry)

    # Copy all console files into the jail
    action_copylist(install_list.list_console, 'jail/opt/ivle', dry)

    # TODO: Copy operating system files into the jail

    # Compile .py files into .pyc or .pyo files
    compileall.compile_dir('www', quiet=True)
    compileall.compile_dir('console', quiet=True)

    return 0

def install(args):
    # Create the target directory
    nojail = False  # Set to True later if --nojail
    dry = False     # Set to True later if --dry

    if not dry and os.geteuid() != 0:
        print >>sys.stderr, "Must be root to run install"
        print >>sys.stderr, "(I need to chown some files)."
        return 1

    # Create the target (install) directory
    action_mkdir(ivle_install_dir, dry)

    # Create bin and copy the compiled files there
    action_mkdir(os.path.join(ivle_install_dir, 'bin'), dry)
    tramppath = os.path.join(ivle_install_dir, 'bin/trampoline')
    action_copyfile('trampoline/trampoline', tramppath, dry)
    # chown trampoline to root and set setuid bit
    action_chown_setuid(tramppath, dry)

    # Copy the www directory using the list
    action_copylist(install_list.list_www, ivle_install_dir, dry)

    if not nojail:
        # Copy the local jail directory built by the build action
        # to the jails template directory (it will be used as a template
        # for all the students' jails).
        action_copytree('jail', os.path.join(jail_base, 'template'), dry)

    return 0

# The actions call Python os functions but print actions and handle dryness.
# May still throw os exceptions if errors occur.

class RunError:
    """Represents an error when running a program (nonzero return)."""
    def __init__(self, prog, retcode):
        self.prog = prog
        self.retcode = retcode
    def __str__(self):
        return str(self.prog) + " returned " + repr(self.retcode)

def action_runprog(prog, args, dry):
    """Runs a unix program. Searches in $PATH. Synchronous (waits for the
    program to return). Runs in the current environment. First prints the
    action as a "bash" line.

    Throws a RunError with a retcode of the return value of the program,
    if the program did not return 0.

    prog: String. Name of the program. (No path required, if in $PATH).
    args: [String]. Arguments to the program.
    dry: Bool. If True, prints but does not execute.
    """
    print prog, string.join(args, ' ')
    if dry: return
    ret = os.spawnvp(os.P_WAIT, prog, args)
    if ret != 0:
        raise RunError(prog, ret)

def action_mkdir(path, dry):
    """Calls mkdir. Silently ignored if the directory already exists.
    Creates all parent directories as necessary."""
    print "mkdir -p", path
    if dry: return
    try:
        os.makedirs(path)
    except OSError, (err, msg):
        if err != errno.EEXIST:
            raise

def action_copytree(src, dst, dry):
    """Copies an entire directory tree. Symlinks are seen as normal files and
    copies of the entire file (not the link) are made. Creates all parent
    directories as necessary.

    See shutil.copytree."""
    if os.access(dst, os.F_OK):
        print "rm -r", dst
        if not dry:
            shutil.rmtree(dst, True)
    print "cp -r", src, dst
    if dry: return
    shutil.copytree(src, dst)

def action_copylist(srclist, dst, dry):
    """Copies all files in a list to a new location. The files in the list
    are read relative to the current directory, and their destinations are the
    same paths relative to dst. Creates all parent directories as necessary.
    """
    for srcfile in srclist:
        dstfile = os.path.join(dst, srcfile)
        dstdir = os.path.split(dstfile)[0]
        if not os.path.isdir(dstdir):
            action_mkdir(dstdir, dry)
        print "cp -f", srcfile, dstfile
        if not dry:
            shutil.copyfile(srcfile, dstfile)

def action_copyfile(src, dst, dry):
    """Copies one file to a new location. Creates all parent directories
    as necessary.
    """
    dstdir = os.path.split(dst)[0]
    if not os.path.isdir(dstdir):
        action_mkdir(dstdir, dry)
    print "cp -f", src, dst
    if not dry:
        shutil.copyfile(src, dst)

def action_chown_setuid(file, dry):
    """Chowns a file to root, and sets the setuid bit on the file.
    Calling this function requires the euid to be root.
    The actual mode of path is set to: rws--s--s
    """
    print "chown root:root", file
    if not dry:
        os.chown(file, 0, 0)
    print "chmod a+xs", file
    print "chmod u+rw", file
    if not dry:
        os.chmod(file, stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            | stat.S_ISUID | stat.S_IRUSR | stat.S_IWUSR)

def query_user(default, prompt):
    """Prompts the user for a string, which is read from a line of stdin.
    Exits silently if EOF is encountered. Returns the string, with spaces
    removed from the beginning and end.

    Returns default if a 0-length line (after spaces removed) was read.
    """
    sys.stdout.write('%s\n    (default: "%s")\n>' % (prompt, default))
    try:
        val = sys.stdin.readline()
    except KeyboardInterrupt:
        # Ctrl+C
        sys.stdout.write("\n")
        sys.exit(1)
    sys.stdout.write("\n")
    # If EOF, exit
    if val == '': sys.exit(1)
    # If empty line, return default
    val = val.strip()
    if val == '': return default
    return val

def filter_mutate(function, list):
    """Like built-in filter, but mutates the given list instead of returning a
    new one. Returns None."""
    i = len(list)-1
    while i >= 0:
        # Delete elements which do not match
        if not function(list[i]):
            del list[i]
        i -= 1

if __name__ == "__main__":
    sys.exit(main())
