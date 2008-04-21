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
# Creates lib/conf/conf.py and trampoline/conf.h.

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
import hashlib
import uuid
import pysvn

# Import modules from the website is tricky since they're in the www
# directory.
sys.path.append(os.path.join(os.getcwd(), 'lib'))
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
    # Needed by fileservice
    '/lib/libcom_err.so.2',
    '/lib/libcrypt.so.1',
    '/lib/libkeyutils.so.1',
    '/lib/libresolv.so.2',
    '/lib/librt.so.1',
    '/lib/libuuid.so.1',
    '/usr/lib/libapr-1.so.0',
    '/usr/lib/libaprutil-1.so.0',
    '/usr/lib/libdb-4.4.so',
    '/usr/lib/libexpat.so.1',
    '/usr/lib/libgcrypt.so.11',
    '/usr/lib/libgnutls.so.13',
    '/usr/lib/libgpg-error.so.0',
    '/usr/lib/libgssapi_krb5.so.2',
    '/usr/lib/libk5crypto.so.3',
    '/usr/lib/libkrb5.so.3',
    '/usr/lib/libkrb5support.so.0',
    '/usr/lib/liblber.so.2',
    '/usr/lib/libldap_r.so.2',
    '/usr/lib/libneon.so.26',
    '/usr/lib/libpq.so.5',
    '/usr/lib/libsasl2.so.2',
    '/usr/lib/libsqlite3.so.0',
    '/usr/lib/libsvn_client-1.so.1',
    '/usr/lib/libsvn_delta-1.so.1',
    '/usr/lib/libsvn_diff-1.so.1',
    '/usr/lib/libsvn_fs-1.so.1',
    '/usr/lib/libsvn_fs_base-1.so.1',
    '/usr/lib/libsvn_fs_fs-1.so.1',
    '/usr/lib/libsvn_ra-1.so.1',
    '/usr/lib/libsvn_ra_dav-1.so.1',
    '/usr/lib/libsvn_ra_local-1.so.1',
    '/usr/lib/libsvn_ra_svn-1.so.1',
    '/usr/lib/libsvn_repos-1.so.1',
    '/usr/lib/libsvn_subr-1.so.1',
    '/usr/lib/libsvn_wc-1.so.1',
    '/usr/lib/libtasn1.so.3',
    '/usr/lib/libxml2.so.2',
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
    # Needed for resolv
    '/lib/libnss_dns.so.2',
    '/lib/libnss_mdns4_minimal.so.2',
    '/etc/hosts',
    '/etc/resolv.conf',
    #'/etc/hosts.conf',
    #'/etc/hostname',
    '/etc/nsswitch.conf',
    '/lib/libnss_files.so.2',
    # Needed for PIL
    '/usr/lib/libjpeg.so.62',
    # Needed by lxml
    '/usr/lib/libxslt.so.1',
    '/usr/lib/libexslt.so.0',
    # Needed by elementtree
    '/usr/lib/libtidy-0.99.so.0',
]
# Symlinks to make within the jail. Src mapped to dst.
JAIL_LINKS = {
    'python%s' % PYTHON_VERSION: 'jail/usr/bin/python',
}
# Trees to copy. Src mapped to dst (these will be passed to action_copytree).
JAIL_COPYTREES = {
    '/usr/lib/python%s' % PYTHON_VERSION:
        'jail/usr/lib/python%s' % PYTHON_VERSION,
    '/var/lib/python-support/python%s' % PYTHON_VERSION:
        'jail/var/lib/python-support/python%s' %PYTHON_VERSION,
    '/usr/share/matplotlib': 'jail/usr/share/matplotlib',
    '/etc/ld.so.conf.d': 'jail/etc/ld.so.conf.d',
    '/usr/share/pycentral': 'jail/usr/share/pycentral',
    '/usr/share/pycentral-data': 'jail/usr/share/pycentral-data',
    '/usr/share/nltk': 'jail/usr/share/nltk',
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
config_options.append(ConfigOption("root_dir", "/",
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
    """Location of Directories
=======================
Root directory where the jails (containing user files) are stored
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
config_options.append(ConfigOption("exercises_base",
    "/home/informatics/exercises",
    """Root directory where the exercise directories (containing
subject-independent exercise sheets) are stored (on the local file
system):""",
    """
# In the local file system, where are the subject-independent exercise sheet
# file spaces located."""))
config_options.append(ConfigOption("tos_path",
    "/home/informatics/tos.html",
    """Location where the Terms of Service document is stored (on the local
    file system):""",
    """
# In the local file system, where is the Terms of Service document located."""))
config_options.append(ConfigOption("motd_path",
    "/home/informatics/motd.html",
    """Location where the Message of the Day document is stored (on the local
    file system):""",
    """
# In the local file system, where is the Message of the Day document
# located. This is an HTML file (just the body fragment), which will
# be displayed on the login page. It is optional."""))
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
config_options.append(ConfigOption("db_dbname", "ivle",
    """Database name:""",
    """
# Database name"""))
config_options.append(ConfigOption("db_forumdbname", "ivle_forum",
    """Forum Database name:""",
    """
# Forum Database name"""))
config_options.append(ConfigOption("db_user", "postgres",
    """Username for DB server login:""",
    """
# Database username"""))
config_options.append(ConfigOption("db_password", "",
    """Password for DB server login:
    (Caution: This password is stored in plaintext in lib/conf/conf.py)""",
    """
# Database password"""))
config_options.append(ConfigOption("auth_modules", "ldap_auth",
    """Authentication config
=====================
Comma-separated list of authentication modules. Only "ldap" is available
by default.""",
    """
# Comma-separated list of authentication modules.
# These refer to importable Python modules in the www/auth directory.
# Modules "ldap" and "guest" are available in the source tree, but
# other modules may be plugged in to auth against organisation-specific
# auth backends."""))
config_options.append(ConfigOption("ldap_url", "ldaps://www.example.com",
    """(LDAP options are only relevant if "ldap" is included in the list of
auth modules).
URL for LDAP authentication server:""",
    """
# URL for LDAP authentication server"""))
config_options.append(ConfigOption("ldap_format_string",
    "uid=%s,ou=users,o=example",
    """Format string for LDAP auth request:
    (Must contain a single "%s" for the user's login name)""",
    """
# Format string for LDAP auth request
# (Must contain a single "%s" for the user's login name)"""))
config_options.append(ConfigOption("svn_addr", "http://svn.localhost/",
    """Subversion config
=================
The base url for accessing subversion repositories:""",
    """
# The base url for accessing subversion repositories."""))
config_options.append(ConfigOption("svn_conf", "/opt/ivle/svn/svn.conf",
    """The location of the subversion configuration file used by apache
to host the user repositories:""",
    """
# The location of the subversion configuration file used by
# apache to host the user repositories."""))
config_options.append(ConfigOption("svn_repo_path", "/home/informatics/repositories",
    """The root directory for the subversion repositories:""",
    """
# The root directory for the subversion repositories."""))
config_options.append(ConfigOption("svn_auth_ivle", "/opt/ivle/svn/ivle.auth",
    """The location of the password file used to authenticate users
of the subversion repository from the ivle server:""",
    """
# The location of the password file used to authenticate users
# of the subversion repository from the ivle server."""))
config_options.append(ConfigOption("svn_auth_local", "/opt/ivle/svn/local.auth",
    """The location of the password file used to authenticate local users
of the subversion repository:""",
    """
# The location of the password file used to authenticate local users
# of the subversion repository."""))
config_options.append(ConfigOption("usrmgt_host", "localhost",
    """User Management Server config
============================
The hostname where the usrmgt-server runs:""",
    """
# The hostname where the usrmgt-server runs."""))
config_options.append(ConfigOption("usrmgt_port", "2178",
    """The port where the usrmgt-server runs:""",
    """
# The port where the usrmgt-server runs."""))
config_options.append(ConfigOption("usrmgt_magic", "",
    """The password for the usrmgt-server:""",
    """
# The password for the usrmgt-server."""))

# Try importing existing conf, but if we can't just set up defaults
# The reason for this is that these settings are used by other phases
# of setup besides conf, so we need to know them.
# Also this allows you to hit Return to accept the existing value.
try:
    confmodule = __import__("lib/conf/conf")
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
    'text/css', 'image/png', 'image/gif', 'application/xml']

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

Creates lib/conf/conf.py and trampoline/conf.h.

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
--nosubjects    Do not copy the subjects and exercises directories.
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
    list_lib = build_list_py_files('lib')
    list_subjects = build_list_py_files('subjects', no_top_level=True)
    list_exercises = build_list_py_files('exercises', no_top_level=True)
    list_scripts = [
        "scripts/python-console",
        "scripts/fileservice",
        "scripts/serveservice",
        "scripts/usrmgt-server",
        "scripts/diffservice",
    ]
    # Make sure that the files generated by conf are in the list
    # (since listmake is typically run before conf)
    if "lib/conf/conf.py" not in list_lib:
        list_lib.append("lib/conf/conf.py")
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
# List of all installable files in lib directory.
list_lib = """)
        writelist_pretty(file, list_lib)
        file.write("""
# List of all installable files in scripts directory.
list_scripts = """)
        writelist_pretty(file, list_scripts)
        file.write("""
# List of all installable files in subjects directory.
# This is to install sample subjects and material.
list_subjects = """)
        writelist_pretty(file, list_subjects)
        file.write("""
# List of all installable files in exercises directory.
# This is to install sample exercise material.
list_exercises = """)
        writelist_pretty(file, list_exercises)

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
    global db_port, usrmgt_port
    # Set up some variables

    cwd = os.getcwd()
    # the files that will be created/overwritten
    conffile = os.path.join(cwd, "lib/conf/conf.py")
    jailconffile = os.path.join(cwd, "lib/conf/jailconf.py")
    conf_hfile = os.path.join(cwd, "trampoline/conf.h")
    phpBBconffile = os.path.join(cwd, "www/php/phpBB3/config.php")
    usrmgtserver_initdfile = os.path.join(cwd, "doc/setup/usrmgt-server.init")

    # Get command-line arguments to avoid asking questions.

    optnames = []
    for opt in config_options:
        optnames.append(opt.option_name + "=")
    (opts, args) = getopt.gnu_getopt(args, "", optnames)

    if args != []:
        print >>sys.stderr, "Invalid arguments:", string.join(args, ' ')
        return 2

    if opts == []:
        # Interactive mode. Prompt the user for all the values.

        print """This tool will create the following files:
    %s
    %s
    %s
    %s
    %s
prompting you for details about your configuration. The file will be
overwritten if it already exists. It will *not* install or deploy IVLE.

Please hit Ctrl+C now if you do not wish to do this.
""" % (conffile, jailconffile, conf_hfile, phpBBconffile, usrmgtserver_initdfile)

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
    try:
        db_port = int(db_port)
        if db_port < 0 or db_port >= 65536: raise ValueError()
    except ValueError:
        print >>sys.stderr, (
        "Invalid DB port (%s).\n"
        "Must be an integer between 0 and 65535." % repr(db_port))
        return 1
    try:
        usrmgt_port = int(usrmgt_port)
        if usrmgt_port < 0 or usrmgt_port >= 65536: raise ValueError()
    except ValueError:
        print >>sys.stderr, (
        "Invalid user management port (%s).\n"
        "Must be an integer between 0 and 65535." % repr(usrmgt_port))
        return 1

    # Generate the forum secret
    forum_secret = hashlib.md5(uuid.uuid4().bytes).hexdigest()

    # Write lib/conf/conf.py

    try:
        conf = open(conffile, "w")

        conf.write("""# IVLE Configuration File
# conf.py
# Miscellaneous application settings

""")
        for opt in config_options:
            conf.write('%s\n%s = %s\n' % (opt.comment, opt.option_name,
                repr(globals()[opt.option_name])))

	# Add the forum secret to the config file (regenerated each config)
        conf.write('forum_secret = "%s"\n' % (forum_secret))

        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote lib/conf/conf.py"

    # Write conf/jailconf.py

    try:
        conf = open(jailconffile, "w")

        # In the "in-jail" version of conf, we don't need MOST of the details
        # (it would be a security risk to have them here).
        # So we just write root_dir, and jail_base is "/".
        # (jail_base being "/" means "jail-relative" paths are relative to "/"
        # when inside the jail.)
        conf.write("""# IVLE Configuration File
# conf.py
# Miscellaneous application settings
# (User jail version)


# In URL space, where in the site is IVLE located. (All URLs will be prefixed
# with this).
# eg. "/" or "/ivle".
root_dir = %s

# In the local file system, where are the student/user file spaces located.
# The user jails are expected to be located immediately in subdirectories of
# this location.
jail_base = '/'

# The hostname for serving publicly accessible pages
public_host = %s
""" % (repr(root_dir),repr(public_host)))

        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote lib/conf/jailconf.py"

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
""" % (repr(jail_base)[1:-1], repr(allowed_uids_list)[1:-1]))
    # Note: The above uses PYTHON reprs, not C reprs
    # However they should be the same with the exception of the outer
    # characters, which are stripped off and replaced

        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote trampoline/conf.h"

    # Write www/php/phpBB3/config.php

    try:
        conf = open(phpBBconffile, "w")
        
        # php-pg work around
        if db_host == 'localhost':
            forumdb_host = '127.0.0.1'
        else:
            forumdb_host = db_host

        conf.write( """<?php
// phpBB 3.0.x auto-generated configuration file
// Do not change anything in this file!
$dbms = 'postgres';
$dbhost = '""" + forumdb_host + """';
$dbport = '""" + str(db_port) + """';
$dbname = '""" + db_forumdbname + """';
$dbuser = '""" + db_user + """';
$dbpasswd = '""" + db_password + """';

$table_prefix = 'phpbb_';
$acm_type = 'file';
$load_extensions = '';
@define('PHPBB_INSTALLED', true);
// @define('DEBUG', true);
//@define('DEBUG_EXTRA', true);

$forum_secret = '""" + forum_secret +"""';
?>"""   )
    
        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote www/php/phpBB3/config.php"

    # Write lib/conf/usrmgt-server.init

    try:
        conf = open(usrmgtserver_initdfile, "w")

        conf.write( '''#! /bin/sh

# Works for Ubuntu. Check before using on other distributions

### BEGIN INIT INFO
# Provides:          usrmgt-server
# Required-Start:    $syslog $networking $urandom
# Required-Stop:     $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      1
# Short-Description: IVLE user management server
# Description:       Daemon connecting to the IVLE user management database.
### END INIT INFO

PATH=/sbin:/bin:/usr/sbin:/usr/bin
DESC="IVLE user management server"
NAME=usrmgt-server
DAEMON=/opt/ivle/scripts/$NAME
DAEMON_ARGS="''' + str(usrmgt_port) + ''' ''' + usrmgt_magic + '''"
PIDFILE=/var/run/$NAME.pid
SCRIPTNAME=/etc/init.d/usrmgt-server

# Exit if the daemon does not exist 
test -f $DAEMON || exit 0

# Load the VERBOSE setting and other rcS variables
[ -f /etc/default/rcS ] && . /etc/default/rcS

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.0-6) to ensure that this file is present.
. /lib/lsb/init-functions

#
# Function that starts the daemon/service
#
do_start()
{
	# Return
	#   0 if daemon has been started
	#   1 if daemon was already running
	#   2 if daemon could not be started
	start-stop-daemon --start --quiet --pidfile $PIDFILE --exec $DAEMON --test > /dev/null \
		|| return 1
	start-stop-daemon --start --quiet --pidfile $PIDFILE --exec $DAEMON -- \
		$DAEMON_ARGS \
		|| return 2
	# Add code here, if necessary, that waits for the process to be ready
	# to handle requests from services started subsequently which depend
	# on this one.  As a last resort, sleep for some time.
}

#
# Function that stops the daemon/service
#
do_stop()
{
	# Return
	#   0 if daemon has been stopped
	#   1 if daemon was already stopped
	#   2 if daemon could not be stopped
	#   other if a failure occurred
	start-stop-daemon --stop --quiet --retry=TERM/30/KILL/5 --pidfile $PIDFILE --name $NAME
	RETVAL="$?"
	[ "$RETVAL" = 2 ] && return 2
	# Wait for children to finish too if this is a daemon that forks
	# and if the daemon is only ever run from this initscript.
	# If the above conditions are not satisfied then add some other code
	# that waits for the process to drop all resources that could be
	# needed by services started subsequently.  A last resort is to
	# sleep for some time.
	start-stop-daemon --stop --quiet --oknodo --retry=0/30/KILL/5 --exec $DAEMON
	[ "$?" = 2 ] && return 2
	# Many daemons don't delete their pidfiles when they exit.
	rm -f $PIDFILE
	return "$RETVAL"
}

#
# Function that sends a SIGHUP to the daemon/service
#
do_reload() {
	#
	# If the daemon can reload its configuration without
	# restarting (for example, when it is sent a SIGHUP),
	# then implement that here.
	#
	start-stop-daemon --stop --signal 1 --quiet --pidfile $PIDFILE --name $NAME
	return 0
}

case "$1" in
  start)
    [ "$VERBOSE" != no ] && log_daemon_msg "Starting $DESC" "$NAME"
	do_start
	case "$?" in
		0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
		2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
	esac
	;;
  stop)
	[ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC" "$NAME"
	do_stop
	case "$?" in
		0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
		2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
	esac
	;;
  #reload|force-reload)
	#
	# If do_reload() is not implemented then leave this commented out
	# and leave 'force-reload' as an alias for 'restart'.
	#
	#log_daemon_msg "Reloading $DESC" "$NAME"
	#do_reload
	#log_end_msg $?
	#;;
  restart|force-reload)
	#
	# If the "reload" option is implemented then remove the
	# 'force-reload' alias
	#
	log_daemon_msg "Restarting $DESC" "$NAME"
	do_stop
	case "$?" in
	  0|1)
		do_start
		case "$?" in
			0) log_end_msg 0 ;;
			1) log_end_msg 1 ;; # Old process is still running
			*) log_end_msg 1 ;; # Failed to start
		esac
		;;
	  *)
	  	# Failed to stop
		log_end_msg 1
		;;
	esac
	;;
  *)
	#echo "Usage: $SCRIPTNAME {start|stop|restart|reload|force-reload}" >&2
	echo "Usage: $SCRIPTNAME {start|stop|restart|force-reload}" >&2
	exit 3
	;;
esac

:
''')
        
        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    # fix permissions as the file contains the database password
    try:
        os.chmod('doc/setup/usrmgt-server.init', 0600)
    except OSError, (errno, strerror):
        print "WARNING: Couldn't chmod doc/setup/usrmgt-server.init:"
        print "OS error(%s): %s" % (errno, strerror)

    print "Successfully wrote lib/conf/usrmgt-server.init"

    print
    print "You may modify the configuration at any time by editing"
    print conffile
    print jailconffile
    print conf_hfile
    print phpBBconffile
    print usrmgtserver_initdfile
    print
    return 0

def build(args):
    # Get "dry" variable from command line
    (opts, args) = getopt.gnu_getopt(args, "n", ['dry'])
    opts = dict(opts)
    dry = '-n' in opts or '--dry' in opts

    if dry:
        print "Dry run (no actions will be executed\n"
    
    # Find out the revison number
    revnum = get_svn_revision()
    print "Building Revision %s"%str(revnum)
    if not dry:
        vfile = open('BUILD-VERSION','w')
        vfile.write(str(revnum) + '\n')
        vfile.close()

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

    # Chmod the tmp directory to world writable
    action_chmod_w('jail/tmp', dry)

    # Copy all console and operating system files into the jail
    action_copylist(install_list.list_scripts, 'jail/opt/ivle', dry)
    copy_os_files_jail(dry)
    # Chmod the python console
    action_chmod_x('jail/opt/ivle/scripts/python-console', dry)
    action_chmod_x('jail/opt/ivle/scripts/fileservice', dry)
    action_chmod_x('jail/opt/ivle/scripts/serveservice', dry)
    
    # Also copy the IVLE lib directory into the jail
    # This is necessary for running certain scripts
    action_copylist(install_list.list_lib, 'jail/opt/ivle', dry)
    # IMPORTANT: The file jail/opt/ivle/lib/conf/conf.py contains details
    # which could compromise security if left in the jail (such as the DB
    # password).
    # The "safe" version is in jailconf.py. Delete conf.py and replace it with
    # jailconf.py.
    action_copyfile('lib/conf/jailconf.py',
        'jail/opt/ivle/lib/conf/conf.py', dry)

    # Compile .py files into .pyc or .pyo files
    compileall.compile_dir('www', quiet=True)
    compileall.compile_dir('lib', quiet=True)
    compileall.compile_dir('scripts', quiet=True)
    compileall.compile_dir('jail/opt/ivle/lib', quiet=True)

    # Set up ivle.pth inside the jail
    # Need to set /opt/ivle/lib to be on the import path
    ivle_pth = \
        "jail/usr/lib/python%s/site-packages/ivle.pth" % PYTHON_VERSION
    f = open(ivle_pth, 'w')
    f.write('/opt/ivle/lib\n')
    f.close()

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

    # Create a scripts directory to put the usrmgt-server in.
    action_mkdir(os.path.join(ivle_install_dir, 'scripts'), dry)
    usrmgtpath = os.path.join(ivle_install_dir, 'scripts/usrmgt-server')
    action_copyfile('scripts/usrmgt-server', usrmgtpath, dry)
    action_chmod_x(usrmgtpath, dry)

    # Copy the www and lib directories using the list
    action_copylist(install_list.list_www, ivle_install_dir, dry)
    action_copylist(install_list.list_lib, ivle_install_dir, dry)
    
    # Copy the php directory
    forum_dir = "www/php/phpBB3"
    forum_path = os.path.join(ivle_install_dir, forum_dir)
    action_copytree(forum_dir, forum_path, dry)
    print "chown -R www-data:www-data %s" % forum_path
    if not dry:
        os.system("chown -R www-data:www-data %s" % forum_path)

    if not nojail:
        # Copy the local jail directory built by the build action
        # to the jails template directory (it will be used as a template
        # for all the students' jails).
        action_copytree('jail', os.path.join(jail_base, 'template'), dry)
    if not nosubjects:
        # Copy the subjects and exercises directories across
        action_copylist(install_list.list_subjects, subjects_base, dry,
            srcdir="./subjects")
        action_copylist(install_list.list_exercises, exercises_base, dry,
            srcdir="./exercises")

    # Append IVLE path to ivle.pth in python site packages
    # (Unless it's already there)
    ivle_pth = os.path.join(sys.prefix,
        "lib/python%s/site-packages/ivle.pth" % PYTHON_VERSION)
    ivle_www = os.path.join(ivle_install_dir, "www")
    ivle_lib = os.path.join(ivle_install_dir, "lib")
    write_ivle_pth = True
    write_ivle_lib_pth = True
    try:
        file = open(ivle_pth, 'r')
        for line in file:
            if line.strip() == ivle_www:
                write_ivle_pth = False
            elif line.strip() == ivle_lib:
                write_ivle_lib_pth = False
        file.close()
    except (IOError, OSError):
        pass
    if write_ivle_pth:
        action_append(ivle_pth, ivle_www)
    if write_ivle_lib_pth:
        action_append(ivle_pth, ivle_lib)

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

def action_remove(path, dry):
    """Calls rmtree, deleting the target file if it exists."""
    try:
        print "rm -r", path
        if not dry:
            shutil.rmtree(path, True)
    except OSError, (err, msg):
        if err != errno.EEXIST:
            raise
        # Otherwise, didn't exist, so we don't care

def action_rename(src, dst, dry):
    """Calls rename. Deletes the target if it already exists."""
    action_remove(dst, dry)
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
    # Allow copying over itself
    if (os.path.normpath(os.path.join(os.getcwd(),src)) ==
        os.path.normpath(os.path.join(os.getcwd(),dst))):
        return
    action_remove(dst, dry)
    print "cp -r", src, dst
    if dry: return
    shutil.copytree(src, dst, True)

def action_linktree(src, dst, dry):
    """Hard-links an entire directory tree. Same as copytree but the created
    files are hard-links not actual copies. Removes the existing destination.
    """
    action_remove(dst, dry)
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
    """Chmod 755 a file (sets permissions to rwxr-xr-x)."""
    print "chmod 755", file
    if not dry:
        os.chmod(file, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR
            | stat.S_IXGRP | stat.S_IRGRP | stat.S_IXOTH | stat.S_IROTH)


def action_chmod_w(file, dry):
    """Chmod 777 a file (sets permissions to rwxrwxrwx)."""
    print "chmod 777", file
    if not dry:
        os.chmod(file, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR
            | stat.S_IXGRP | stat.S_IWGRP | stat.S_IRGRP | stat.S_IXOTH
            | stat.S_IWOTH | stat.S_IROTH)

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

def get_svn_revision():
    """Returns either the current SVN revision of this build, or None"""
    try:
        svn = pysvn.Client()
        entry = svn.info('.')
        revnum = entry.revision.number
    except pysvn.ClientError, e:
        revnum = None
    return revnum

if __name__ == "__main__":
    sys.exit(main())

