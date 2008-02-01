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

# setup.py config [args]
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

# Import modules from the website is tricky since they're in the www
# directory.
sys.path.append(os.path.join(os.getcwd(), 'www'))
import conf
import common.makeuser

# Determine which Python version (2.4 or 2.5, for example) we are running,
# and use that as the filename to the Python directory.
# Just get the first 3 characters of sys.version.
PYTHON_VERSION = sys.version[0:3]

# Operating system files to copy over into the jail.
# These will be copied from the given place on the OS file system into the
# same place within the jail.
JAIL_FILES = [
    '/lib/ld-linux.so.2',
    '/lib/tls/i686/cmov/libc.so.6',
    '/lib/tls/i686/cmov/libdl.so.2',
    '/lib/tls/i686/cmov/libm.so.6',
    '/lib/tls/i686/cmov/libpthread.so.0',
    '/lib/tls/i686/cmov/libutil.so.1',
    '/etc/ld.so.conf',
    '/etc/ld.so.cache',
    # These 2 files do not exist in Ubuntu
    #'/etc/ld.so.preload',
    #'/etc/ld.so.nohwcap',
    # UNIX commands
    '/usr/bin/strace',
    '/bin/ls',
    '/bin/echo',
    # Needed by python
    '/usr/bin/python%s' % PYTHON_VERSION,
    # Needed by matplotlib
    '/usr/lib/i686/cmov/libssl.so.0.9.8',
    '/usr/lib/i686/cmov/libcrypto.so.0.9.8',
    '/lib/tls/i686/cmov/libnsl.so.1',
    '/usr/lib/libz.so.1',
    '/usr/lib/atlas/liblapack.so.3',
    '/usr/lib/atlas/libblas.so.3',
    '/usr/lib/libg2c.so.0',
    '/usr/lib/libstdc++.so.6',
    '/usr/lib/libfreetype.so.6',
    '/usr/lib/libpng12.so.0',
    '/usr/lib/libBLT.2.4.so.8.4',
    '/usr/lib/libtk8.4.so.0',
    '/usr/lib/libtcl8.4.so.0',
    '/usr/lib/tcl8.4/init.tcl',
    '/usr/lib/libX11.so.6',
    '/usr/lib/libXau.so.6',
    '/usr/lib/libXdmcp.so.6',
    '/lib/libgcc_s.so.1',
    '/etc/matplotlibrc',
]
# Symlinks to make within the jail. Src mapped to dst.
JAIL_LINKS = {
    'python%s' % PYTHON_VERSION: 'jail/usr/bin/python',
}
# Trees to copy. Src mapped to dst (these will be passed to action_copytree).
JAIL_COPYTREES = {
    '/usr/lib/python%s' % PYTHON_VERSION:
        'jail/usr/lib/python%s' % PYTHON_VERSION,
    '/usr/share/matplotlib': 'jail/usr/share/matplotlib',
    '/etc/ld.so.conf.d': 'jail/etc/ld.so.conf.d',
}

class ConfigOption:
    """A configuration option; one of the things written to conf.py."""
    def __init__(self, option_name, default, prompt, comment):
        """Creates a configuration option.
        option_name: Name of the variable in conf.py. Also name of the
            command-line argument to setup.py conf.
        default: Default value for this variable.
        prompt: (Short) string presented during the interactive prompt in
            setup.py conf.
        comment: (Long) comment string stored in conf.py. Each line of this
            string should begin with a '#'.
        """
        self.option_name = option_name
        self.default = default
        self.prompt = prompt
        self.comment = comment

# Configuration options, defaults and descriptions
config_options = []
config_options.append(ConfigOption("root_dir", "/ivle",
    """Root directory where IVLE is located (in URL space):""",
    """
# In URL space, where in the site is IVLE located. (All URLs will be prefixed
# with this).
# eg. "/" or "/ivle"."""))
config_options.append(ConfigOption("ivle_install_dir", "/opt/ivle",
    'Root directory where IVLE will be installed (on the local file '
    'system):',
    """
# In the local file system, where IVLE is actually installed.
# This directory should contain the "www" and "bin" directories."""))
config_options.append(ConfigOption("jail_base", "/home/informatics/jails",
    """Root directory where the jails (containing user files) are stored
(on the local file system):""",
    """
# In the local file system, where are the student/user file spaces located.
# The user jails are expected to be located immediately in subdirectories of
# this location."""))
config_options.append(ConfigOption("subjects_base",
    "/home/informatics/subjects",
    """Root directory where the subject directories (containing worksheets
and other per-subject files) are stored (on the local file system):""",
    """
# In the local file system, where are the per-subject file spaces located.
# The individual subject directories are expected to be located immediately
# in subdirectories of this location."""))
config_options.append(ConfigOption("public_host", "public.localhost",
    """Hostname which will cause the server to go into "public mode",
providing login-free access to student's published work:""",
    """
# The server goes into "public mode" if the browser sends a request with this
# host. This is for security reasons - we only serve public student files on a
# separate domain to the main IVLE site.
# Public mode does not use cookies, and serves only public content.
# Private mode (normal mode) requires login, and only serves files relevant to
# the logged-in user."""))
config_options.append(ConfigOption("allowed_uids", "33",
    """UID of the web server process which will run IVLE.
Only this user may execute the trampoline. May specify multiple users as
a comma-separated list.
    (eg. "1002,78")""",
    """
# The User-ID of the web server process which will run IVLE, and any other
# users who are allowed to run the trampoline. This is stores as a string of
# comma-separated integers, simply because it is not used within Python, only
# used by the setup program to write to conf.h (see setup.py config)."""))
config_options.append(ConfigOption("db_host", "localhost",
    """PostgreSQL Database config
==========================
Hostname of the DB server:""",
    """
### PostgreSQL Database config ###
# Database server hostname"""))
config_options.append(ConfigOption("db_port", "5432",
    """Port of the DB server:""",
    """
# Database server port"""))
config_options.append(ConfigOption("db_user", "postgres",
    """Username for DB server login:""",
    """
# Database username"""))
config_options.append(ConfigOption("db_password", "",
    """Password for DB server login:
    (Caution: This password is stored in plaintext in www/conf/conf.py)""",
    """
# Database password"""))

# Try importing existing conf, but if we can't just set up defaults
# The reason for this is that these settings are used by other phases
# of setup besides conf, so we need to know them.
# Also this allows you to hit Return to accept the existing value.
try:
    confmodule = __import__("www/conf/conf")
    for opt in config_options:
        try:
            globals()[opt.option_name] = confmodule.__dict__[opt.option_name]
        except:
            globals()[opt.option_name] = opt.default
except ImportError:
    # Just set reasonable defaults
    for opt in config_options:
        globals()[opt.option_name] = opt.default

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
    'text/css', 'image/png', 'application/xml']

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

    # Disallow run as root unless installing
    if (operation != 'install' and operation != 'updatejails'
        and os.geteuid() == 0):
        print >>sys.stderr, "I do not want to run this stage as root."
        print >>sys.stderr, "Please run as a normal user."
        return 1
    # Call the requested operation's function
    try:
        oper_func = {
            'help' : help,
            'config' : conf,
            'build' : build,
            'listmake' : listmake,
            'install' : install,
            'updatejails' : updatejails,
        }[operation]
    except KeyError:
        print >>sys.stderr, (
            """Invalid operation '%s'. Try python setup.py help."""
            % operation)
        return 1
    return oper_func(argv[2:])

# Operation functions

def help(args):
    if args == []:
        print """Usage: python setup.py operation [args]
Operation (and args) can be:
    help [operation]
    listmake (developer use only)
    config [args]
    build
    install [--nojail] [--nosubjects] [-n|--dry]
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
    elif operation == 'config':
        print """python setup.py config [args]
Configures IVLE with machine-specific details, most notably, various paths.
Either prompts the administrator for these details or accepts them as
command-line args. Will be interactive only if there are no arguments given.
Takes defaults from existing conf file if it exists.

To run IVLE out of the source directory (allowing development without having
to rebuild/install), just provide ivle_install_dir as the IVLE trunk
directory, and run build/install one time.

Creates www/conf/conf.py and trampoline/conf.h.

Args are:"""
        for opt in config_options:
            print "    --" + opt.option_name
        print """As explained in the interactive prompt or conf.py.
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
        print """sudo python setup.py install [--nojail] [--nosubjects][--dry|-n]
(Requires root)
Create target install directory ($target).
Create $target/bin.
Copy trampoline/trampoline to $target/bin.
chown and chmod the installed trampoline.
Copy www/ to $target.
Copy jail/ to jails template directory (unless --nojail specified).
Copy subjects/ to subjects directory (unless --nosubjects specified).

--nojail        Do not copy the jail.
--nosubjects    Do not copy the subjects.
--dry | -n  Print out the actions but don't do anything."""
    elif operation == 'updatejails':
        print """sudo python setup.py updatejails [--dry|-n]
(Requires root)
Copy jail/ to each subdirectory in jails directory.

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
    list_subjects = build_list_py_files('subjects', no_top_level=True)
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
        file.write("""
# List of all installable files in subjects directory.
# This is to install sample subjects and material.
list_subjects = """)
        writelist_pretty(file, list_subjects)

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

def build_list_py_files(dir, no_top_level=False):
    """Builds a list of all py files found in a directory and its
    subdirectories. Returns this as a list of strings.
    no_top_level=True means the file paths will not include the top-level
    directory.
    """
    pylist = []
    for (dirpath, dirnames, filenames) in os.walk(dir):
        # Exclude directories beginning with a '.' (such as '.svn')
        filter_mutate(lambda x: x[0] != '.', dirnames)
        # All *.py files are added to the list
        pylist += [os.path.join(dirpath, item) for item in filenames
            if mimetypes.guess_type(item)[0] in listmake_mimetypes]
    if no_top_level:
        for i in range(0, len(pylist)):
            _, pylist[i] = pylist[i].split(os.sep, 1)
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
    global root_dir, ivle_install_dir, jail_base, subjects_base
    global public_host, allowed_uids
    # Set up some variables

    cwd = os.getcwd()
    # the files that will be created/overwritten
    conffile = os.path.join(cwd, "www/conf/conf.py")
    conf_hfile = os.path.join(cwd, "trampoline/conf.h")

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

        for opt in config_options:
            globals()[opt.option_name] = \
                query_user(globals()[opt.option_name], opt.prompt)
    else:
        opts = dict(opts)
        # Non-interactive mode. Parse the options.
        for opt in config_options:
            if '--' + opt.option_name in opts:
                globals()[opt.option_name] = opts['--' + opt.option_name]

    # Error handling on input values
    try:
        allowed_uids_list = map(int, allowed_uids.split(','))
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

""")
        for opt in config_options:
            conf.write('%s\n%s = "%s"\n' % (opt.comment, opt.option_name,
                globals()[opt.option_name]))

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
""" % (jail_base, repr(allowed_uids_list)[1:-1]))

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
    # Get "dry" variable from command line
    (opts, args) = getopt.gnu_getopt(args, "n", ['dry'])
    opts = dict(opts)
    dry = '-n' in opts or '--dry' in opts

    if dry:
        print "Dry run (no actions will be executed\n"

    # Compile the trampoline
    curdir = os.getcwd()
    os.chdir('trampoline')
    action_runprog('make', [], dry)
    os.chdir(curdir)

    # Create the jail and its subdirectories
    # Note: Other subdirs will be made by copying files
    action_mkdir('jail', dry)
    action_mkdir('jail/home', dry)
    action_mkdir('jail/tmp', dry)

    # Copy all console and operating system files into the jail
    action_copylist(install_list.list_console, 'jail/opt/ivle', dry)
    copy_os_files_jail(dry)
    # Chmod the python console
    action_chmod_x('jail/opt/ivle/console/python-console', dry)
    

    # Compile .py files into .pyc or .pyo files
    compileall.compile_dir('www', quiet=True)
    compileall.compile_dir('console', quiet=True)

    return 0

def copy_os_files_jail(dry):
    """Copies necessary Operating System files from their usual locations
    into the jail/ directory of the cwd."""
    # Currently source paths are configured for Ubuntu.
    for filename in JAIL_FILES:
        copy_file_to_jail(filename, dry)
    for src, dst in JAIL_LINKS.items():
        action_symlink(src, dst, dry)
    for src, dst in JAIL_COPYTREES.items():
        action_copytree(src, dst, dry)

def copy_file_to_jail(src, dry):
    """Copies a single file from an absolute location into the same location
    within the jail. src must begin with a '/'. The jail will be located
    in a 'jail' subdirectory of the current path."""
    action_copyfile(src, 'jail' + src, dry)

def install(args):
    # Get "dry" and "nojail" variables from command line
    (opts, args) = getopt.gnu_getopt(args, "n",
        ['dry', 'nojail', 'nosubjects'])
    opts = dict(opts)
    dry = '-n' in opts or '--dry' in opts
    nojail = '--nojail' in opts
    nosubjects = '--nosubjects' in opts

    if dry:
        print "Dry run (no actions will be executed\n"

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
    if not nosubjects:
        # Copy the subjects directory across
        action_copylist(install_list.list_subjects, subjects_base, dry,
            srcdir="./subjects")

    # Append IVLE path to ivle.pth in python site packages
    # (Unless it's already there)
    ivle_pth = os.path.join(sys.prefix,
        "lib/python%s/site-packages/ivle.pth" % PYTHON_VERSION)
    ivle_www = os.path.join(ivle_install_dir, "www")
    write_ivle_pth = True
    try:
        file = open(ivle_pth, 'r')
        for line in file:
            if line.strip() == ivle_www:
                write_ivle_pth = False
                break
    except (IOError, OSError):
        pass
    if write_ivle_pth:
        action_append(ivle_pth, ivle_www)

    return 0

def updatejails(args):
    # Get "dry" variable from command line
    (opts, args) = getopt.gnu_getopt(args, "n", ['dry'])
    opts = dict(opts)
    dry = '-n' in opts or '--dry' in opts

    if dry:
        print "Dry run (no actions will be executed\n"

    if not dry and os.geteuid() != 0:
        print >>sys.stderr, "Must be root to run install"
        print >>sys.stderr, "(I need to chown some files)."
        return 1

    # Update the template jail directory in case it hasn't been installed
    # recently.
    action_copytree('jail', os.path.join(jail_base, 'template'), dry)

    # Re-link all the files in all students jails.
    for dir in os.listdir(jail_base):
        if dir == 'template': continue
        # First back up the student's home directory
        temp_home = os.tmpnam()
        action_rename(os.path.join(jail_base, dir, 'home'), temp_home, dry)
        # Delete the student's jail and relink the jail files
        action_linktree(os.path.join(jail_base, 'template'),
            os.path.join(jail_base, dir), dry)
        # Restore the student's home directory
        action_rename(temp_home, os.path.join(jail_base, dir, 'home'), dry)
        # Set up the user's home directory just in case they don't have a
        # directory for this yet
        action_mkdir(os.path.join(jail_base, dir, 'home', dir), dry)

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

def action_rename(src, dst, dry):
    """Calls rename. Deletes the target if it already exists."""
    if os.access(dst, os.F_OK):
        print "rm -r", dst
        if not dry:
            shutil.rmtree(dst, True)
    print "mv ", src, dst
    if dry: return
    try:
        os.rename(src, dst)
    except OSError, (err, msg):
        if err != errno.EEXIST:
            raise

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
    shutil.copytree(src, dst, True)

def action_linktree(src, dst, dry):
    """Hard-links an entire directory tree. Same as copytree but the created
    files are hard-links not actual copies. Removes the existing destination.
    """
    if os.access(dst, os.F_OK):
        print "rm -r", dst
        if not dry:
            shutil.rmtree(dst, True)
    print "<cp with hardlinks> -r", src, dst
    if dry: return
    common.makeuser.linktree(src, dst)

def action_copylist(srclist, dst, dry, srcdir="."):
    """Copies all files in a list to a new location. The files in the list
    are read relative to the current directory, and their destinations are the
    same paths relative to dst. Creates all parent directories as necessary.
    srcdir is "." by default, can be overridden.
    """
    for srcfile in srclist:
        dstfile = os.path.join(dst, srcfile)
        srcfile = os.path.join(srcdir, srcfile)
        dstdir = os.path.split(dstfile)[0]
        if not os.path.isdir(dstdir):
            action_mkdir(dstdir, dry)
        print "cp -f", srcfile, dstfile
        if not dry:
            try:
                shutil.copyfile(srcfile, dstfile)
                shutil.copymode(srcfile, dstfile)
            except shutil.Error:
                pass

def action_copyfile(src, dst, dry):
    """Copies one file to a new location. Creates all parent directories
    as necessary.
    Warn if file not found.
    """
    dstdir = os.path.split(dst)[0]
    if not os.path.isdir(dstdir):
        action_mkdir(dstdir, dry)
    print "cp -f", src, dst
    if not dry:
        try:
            shutil.copyfile(src, dst)
            shutil.copymode(src, dst)
        except (shutil.Error, IOError), e:
            print "Warning: " + str(e)

def action_symlink(src, dst, dry):
    """Creates a symlink in a given location. Creates all parent directories
    as necessary.
    """
    dstdir = os.path.split(dst)[0]
    if not os.path.isdir(dstdir):
        action_mkdir(dstdir, dry)
    # Delete existing file
    if os.path.exists(dst):
        os.remove(dst)
    print "ln -fs", src, dst
    if not dry:
        os.symlink(src, dst)

def action_append(ivle_pth, ivle_www):
    file = open(ivle_pth, 'a+')
    file.write(ivle_www + '\n')
    file.close()

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

def action_chmod_x(file, dry):
    """Chmod +xs a file (sets execute permission)."""
    print "chmod u+rwx", file
    if not dry:
        os.chmod(file, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR)

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
