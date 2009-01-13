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

# Module: setup/config
# Author: Matt Giuca, Refactored by David Coles
# Date:   03/07/2008

# setup/config.py
# Configures IVLE with machine-specific details, most notably, various paths.
# Either prompts the administrator for these details or accepts them as
# command-line args.
# Creates lib/conf/conf.py and bin/trampoline/conf.h.

import optparse
import getopt
import os
import sys
import hashlib
import uuid

from setup.util import query_user

class ConfigOption:
    """A configuration option; one of the things written to conf.py."""
    def __init__(self, option_name, default, prompt, comment, ask=True):
        """Creates a configuration option.
        option_name: Name of the variable in conf.py. Also name of the
            command-line argument to setup.py conf.
        default: Default value for this variable.
        prompt: (Short) string presented during the interactive prompt in
            setup.py conf.
        comment: (Long) comment string stored in conf.py. Each line of this
            string should begin with a '#'.
        ask: Whether to ask the question in the default config run.
        """
        self.option_name = option_name
        self.default = default
        self.prompt = prompt
        self.comment = comment
        self.ask = ask

# Configuration options, defaults and descriptions
config_options = []

config_options.append(ConfigOption("root_dir", "/",
    """Root directory where IVLE is located (in URL space):""",
    """
# In URL space, where in the site is IVLE located. (All URLs will be prefixed
# with this).
# eg. "/" or "/ivle".""", ask=False))

config_options.append(ConfigOption("prefix", "/usr/local",
    """In the local file system, the prefix to the system directory where IVLE
is installed. (This should either be /usr or /usr/local):""",
    """
# In the local file system, the prefix to the system directory where IVLE is
# installed. This should either be '/usr' or '/usr/local'.
# ('/usr/local' for the usual install, '/usr' for distribution packages)""",
    ask=False))

config_options.append(ConfigOption("python_site_packages_override",
    None,
    """site-packages directory in Python, where Python libraries are to be
installed. May be left as the default, in which case the value will be
computed from prefix and the current Python version:""",
    """
# 'site-packages' directory in Python, where Python libraries are to be
# installed. May be None (recommended), in which case the value will be
# computed from prefix and the current Python version.""", ask=False))

config_options.append(ConfigOption("data_path",
    "/var/lib/ivle",
    "In the local file system, where user-modifiable data files should be "
    "located:",
    """
# In the local file system, where user-modifiable data files should be
# located.""", ask=False))

config_options.append(ConfigOption("log_path",
    "/var/log/ivle",
    """Directory where IVLE log files are stored (on the local
file system). Note - this must be writable by the user the IVLE server 
process runs as (usually www-data):""",
    """
# In the local file system, where IVLE error logs should be located.""",
    ask=False))

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
# used by the setup program to write to conf.h (see setup.py config).""",
    ask=False))

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
    (Caution: This password is stored in plaintext in ivle/conf/conf.py)""",
    """
# Database password"""))

config_options.append(ConfigOption("auth_modules", "",
    """Authentication config
=====================
Comma-separated list of authentication modules.""",
    """
# Comma-separated list of authentication modules.
# Note that auth is always enabled against the local database, and NO OTHER
# auth is enabled by default. This section is for specifying additional auth
# modules.
# These refer to importable Python modules in the www/auth directory.
# Modules "ldap_auth" and "guest" are available in the source tree, but
# other modules may be plugged in to auth against organisation-specific
# auth backends.""", ask=False))

config_options.append(ConfigOption("ldap_url", "ldaps://www.example.com",
    """(LDAP options are only relevant if "ldap" is included in the list of
auth modules).
URL for LDAP authentication server:""",
    """
# URL for LDAP authentication server""", ask=False))

config_options.append(ConfigOption("ldap_format_string",
    "uid=%s,ou=users,o=example",
    """Format string for LDAP auth request:
    (Must contain a single "%s" for the user's login name)""",
    """
# Format string for LDAP auth request
# (Must contain a single "%s" for the user's login name)""", ask=False))

config_options.append(ConfigOption("subject_pulldown_modules", "",
    """Comma-separated list of subject pulldown modules.
Add proprietary modules to automatically enrol students in subjects.""",
    """
# Comma-separated list of subject pulldown modules.
# These refer to importable Python modules in the lib/pulldown_subj directory.
# Only "dummy_subj" is available in the source tree (an example), but
# other modules may be plugged in to pulldown against organisation-specific
# pulldown backends.""", ask=False))

config_options.append(ConfigOption("svn_addr", "http://svn.localhost/",
    """Subversion config
=================
The base url for accessing subversion repositories:""",
    """
# The base url for accessing subversion repositories."""))

config_options.append(ConfigOption("usrmgt_host", "localhost",
    """User Management Server config
============================
The hostname where the usrmgt-server runs:""",
    """
# The hostname where the usrmgt-server runs."""))

config_options.append(ConfigOption("usrmgt_port", "2178",
    """The port where the usrmgt-server runs:""",
    """
# The port where the usrmgt-server runs.""", ask=False))

config_options.append(ConfigOption("usrmgt_magic", None,
    """The password for the usrmgt-server:""",
    """
# The password for the usrmgt-server.""", ask=False))

def configure(args):
    usage = """usage: %prog config [options]
Creates lib/conf/conf.py (and a few other config files).
Interactively asks questions to set this up."""

    # Parse arguments
    parser = optparse.OptionParser(usage)
    (options, args) = parser.parse_args(args)

    # Call the real function
    return __configure(args)

def __configure(args):
    global db_port, usrmgt_port

    # Try importing existing conf, but if we can't just set up defaults
    # The reason for this is that these settings are used by other phases
    # of setup besides conf, so we need to know them.
    # Also this allows you to hit Return to accept the existing value.
    try:
        confmodule = __import__("ivle/conf/conf")
        for opt in config_options:
            try:
                globals()[opt.option_name] = \
                confmodule.__dict__[opt.option_name]
            except:
                globals()[opt.option_name] = opt.default
    except ImportError:
        # Just set reasonable defaults
        for opt in config_options:
            globals()[opt.option_name] = opt.default

    # Set up some variables
    cwd = os.getcwd()

    # the files that will be created/overwritten
    conffile = os.path.join(cwd, "ivle/conf/conf.py")
    jailconffile = os.path.join(cwd, "ivle/conf/jailconf.py")
    conf_hfile = os.path.join(cwd, "bin/trampoline/conf.h")
    phpBBconffile = os.path.join(cwd, "www/php/phpBB3/config.php")

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
prompting you for details about your configuration. The file will be
overwritten if it already exists. It will *not* install or deploy IVLE.

Please hit Ctrl+C now if you do not wish to do this.
""" % (conffile, jailconffile, conf_hfile, phpBBconffile)

        # Get information from the administrator
        # If EOF is encountered at any time during the questioning, just exit
        # silently

        for opt in config_options:
            if opt.ask:
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

    # By default we generate the magic randomly.
    if globals()['usrmgt_magic'] is None:
        globals()['usrmgt_magic'] = hashlib.md5(uuid.uuid4().bytes).hexdigest()

    # Generate the forum secret
    forum_secret = hashlib.md5(uuid.uuid4().bytes).hexdigest()

    # Write lib/conf/conf.py

    try:
        conf = open(conffile, "w")

        conf.write("""# IVLE Configuration File
# conf.py
# Miscellaneous application settings

import os
import sys
""")
        for opt in config_options:
            conf.write('%s\n%s = %r\n' % (opt.comment, opt.option_name,
                globals()[opt.option_name]))

	    # Add the forum secret to the config file (regenerated each config)
        conf.write('forum_secret = "%s"\n\n' % (forum_secret))

        write_conf_file_boilerplate(conf)

        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote %s" % conffile

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

# The URL under which the Subversion repositories are located.
svn_addr = %s
""" % (repr(root_dir),repr(public_host),repr(svn_addr)))

        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote %s" % jailconffile

    # Write bin/trampoline/conf.h

    try:
        conf = open(conf_hfile, "w")

        # XXX Compute jail_base, jail_src_base and jail_system. These will
        # ALSO be done by the boilerplate code, but we need them here in order
        # to write to the C file.
        jail_base = os.path.join(data_path, 'jailmounts')
        jail_src_base = os.path.join(data_path, 'jails')
        jail_system = os.path.join(jail_src_base, '__base__')

        conf.write("""/* IVLE Configuration File
 * conf.h
 * Administrator settings required by trampoline.
 * Note: trampoline will have to be rebuilt in order for changes to this file
 * to take effect.
 */

#define IVLE_AUFS_JAILS

/* In the local file system, where are the jails located.
 * The trampoline does not allow the creation of a jail anywhere besides
 * jail_base or a subdirectory of jail_base.
 */
static const char* jail_base = "%s";
static const char* jail_src_base = "%s";
static const char* jail_system = "%s";

/* Which user IDs are allowed to run the trampoline.
 * This list should be limited to the web server user.
 * (Note that root is an implicit member of this list).
 */
static const int allowed_uids[] = { %s };
""" % (repr(jail_base)[1:-1], repr(jail_src_base)[1:-1],
       repr(jail_system)[1:-1], repr(allowed_uids_list)[1:-1]))
    # Note: The above uses PYTHON reprs, not C reprs
    # However they should be the same with the exception of the outer
    # characters, which are stripped off and replaced

        conf.close()
    except IOError, (errno, strerror):
        print "IO error(%s): %s" % (errno, strerror)
        sys.exit(1)

    print "Successfully wrote %s" % conf_hfile

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

    print "Successfully wrote %s" % phpBBconffile

    print
    print "You may modify the configuration at any time by editing"
    print conffile
    print jailconffile
    print conf_hfile
    print phpBBconffile
    print
    
    return 0

def write_conf_file_boilerplate(conf_file):
    conf_file.write("""\
### Below is boilerplate code, appended by ./setup.py config ###

# Path where architecture-dependent data (including non-user-executable
# binaries) is installed.
lib_path = os.path.join(prefix, 'lib/ivle')

# Path where arch-independent data is installed.
share_path = os.path.join(prefix, 'share/ivle')

# Path where user-executable binaries are installed.
bin_path = os.path.join(prefix, 'bin')

# 'site-packages' directory in Python, where Python libraries are to be
# installed.
if python_site_packages_override is None:
    PYTHON_VERSION = sys.version[0:3]   # eg. "2.5"
    python_site_packages = os.path.join(prefix,
                               'lib/python%s/site-packages' % PYTHON_VERSION)
else:
    python_site_packages = python_site_packages_override

# In the local file system, where the student/user jails will be mounted.
# Only a single copy of the jail's system components will be stored here -
# all user jails will be virtually mounted here.
jail_base = os.path.join(data_path, 'jailmounts')

# In the local file system, where are the student/user file spaces located.
# The user jails are expected to be located immediately in subdirectories of
# this location. Note that no complete jails reside here - only user
# modifications.
jail_src_base = os.path.join(data_path, 'jails')

# In the local file system, where the template system jail will be stored.
jail_system = os.path.join(jail_src_base, '__base__')

# In the local file system, where the subject content files are located.
# (The 'subjects' and 'exercises' directories).
content_path = os.path.join(data_path, 'content')

# In the local file system, where are the per-subject file spaces located.
# The individual subject directories are expected to be located immediately
# in subdirectories of this location.
subjects_base = os.path.join(content_path, 'subjects')

# In the local file system, where are the subject-independent exercise sheet
# file spaces located.
exercises_base = os.path.join(content_path, 'exercises')

# In the local file system, where the system notices are stored (such as terms
# of service and MOTD).
notices_path = os.path.join(data_path, 'notices')

# In the local file system, where is the Terms of Service document located.
tos_path = os.path.join(notices_path, 'tos.html')

# In the local file system, where is the Message of the Day document
# located. This is an HTML file (just the body fragment), which will
# be displayed on the login page. It is optional.
motd_path = os.path.join(notices_path, 'motd.html')

# The location of all the subversion config and repositories.
svn_path = os.path.join(data_path, 'svn')

# The location of the subversion configuration file used by
# apache to host the user repositories.
svn_conf = os.path.join(svn_path, 'svn.conf')

# The location of the subversion configuration file used by
# apache to host the user repositories.
svn_group_conf = os.path.join(svn_path, 'svn-group.conf')

# The root directory for the subversion repositories.
svn_repo_path = os.path.join(svn_path, 'repositories')

# The location of the password file used to authenticate users
# of the subversion repository from the ivle server.
svn_auth_ivle = os.path.join(svn_path, 'ivle.auth')

# The location of the password file used to authenticate local users
# of the subversion repository.
svn_auth_local = os.path.join(svn_path, 'local.auth')
""")
