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
# Creates lib/conf/conf.py and trampoline/conf.h.

import optparse
import getopt
import os
import sys
import hashlib
import uuid
from setup.setuputil import query_user

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
    """Location of jail mountpoints
============================
Root directory where the user jails will be mounted, and the non-user
components of the jails will be stored (on the local file system):""",
    """
# In the local file system, where the student/user jails will be mounted.
# Only a single copy of the jail's system components will be stored here -
# all user jails will be virtually mounted here."""))
config_options.append(ConfigOption("jail_system", "/home/informatics/jails/__base__",
    """Location of system jail components
==================================
Directory where the template system jail will be stored.""",
    """
# In the local file system, where the template system jail will be stored."""))
config_options.append(ConfigOption("jail_src_base", "/home/informatics/jailssrc",
    """Location of user jail components
================================
Root directory where the user components of the jails will be stored (on the
local file system):""",
    """
# In the local file system, where are the student/user file spaces located.
# The user jails are expected to be located immediately in subdirectories of
# this location. Note that no complete jails reside here - only user
# modifications."""))
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
config_options.append(ConfigOption("log_path",
    "/home/informatics/logs",
    """Directory where IVLE log files are stored (on the local
    file system). Note - this must be writable by the user the IVLE server 
    process runs as (usually www-data).:""",
    """
# In the local file system, where IVLE error logs should be located."""))
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
config_options.append(ConfigOption("subject_pulldown_modules", "",
    """Comma-separated list of subject pulldown modules.
Add proprietary modules to automatically enrol students in subjects.""",
    """
# Comma-separated list of subject pulldown modules.
# These refer to importable Python modules in the lib/pulldown_subj directory.
# Only "dummy_subj" is available in the source tree (an example), but
# other modules may be plugged in to pulldown against organisation-specific
# pulldown backends."""))
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

def configure(args):
    usage = """usage: %prog build [options]
(requires root)
Compiles all files and sets up a jail template in the source directory.
-O is recommended to cause compilation to be optimised.
Details:
Compiles (GCC) trampoline/trampoline.c to trampoline/trampoline.
Creates jail with system and student packages installed from MIRROR.
Copies console/ to a location within the jail.
Copies OS programs and files to corresponding locations within the jail
  (eg. python and Python libs, ld.so, etc).
Generates .pyc or .pyo files for all the IVLE .py files."""

    # Parse arguments
    parser = optparse.OptionParser(usage)
    (options, args) = parser.parse_args(args)

    # Call the real function
    __configure(args)

def __configure(args):
    global db_port, usrmgt_port

    # Try importing existing conf, but if we can't just set up defaults
    # The reason for this is that these settings are used by other phases
    # of setup besides conf, so we need to know them.
    # Also this allows you to hit Return to accept the existing value.
    try:
        confmodule = __import__("lib/conf/conf")
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

# The URL under which the Subversion repositories are located.
svn_addr = %s
""" % (repr(root_dir),repr(public_host),repr(svn_addr)))

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
	start-stop-daemon --start --quiet --pidfile $PIDFILE --exec $DAEMON \
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
