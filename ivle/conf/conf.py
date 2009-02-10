# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
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

# Author: Matt Giuca, Will Grant

"""
Temporary emulation layer for the old-style conf.py configuration file.
Loads the IVLE config file and provides all of the legacy config variables.

May raise a RuntimeError on import if it cannot find the config file.
"""

import os
import sys

import configobj

def search_conffile():
    """
    Search for the config file, and return it as a filename.
    1. Environment var IVLECONF (full filename).
    2. ./etc/ivle.conf
    3. /etc/ivle/ivle.conf
    """
    if 'IVLECONF' in os.environ:
        fname = os.environ['IVLECONF']
        if os.path.exists(fname):
            return fname
    if os.path.exists('./etc/ivle.conf'):
        return './etc/ivle.conf'
    if os.path.exists('/etc/ivle/ivle.conf'):
        return '/etc/ivle/ivle.conf'
    raise RuntimeError("Could not find IVLE config file")

conffile = search_conffile()
conf = configobj.ConfigObj(conffile)

CONFIG_OPTIONS = ('root_dir', 'prefix', 'data_path', 'log_path',
    'public_host', 'allowed_uids', 'db_host', 'db_port', 'db_dbname',
    'db_forumdbname', 'db_user', 'db_password', 'auth_modules', 'ldap_url',
    'ldap_format_string', 'subject_pulldown_modules', 'svn_addr',
    'usrmgt_host', 'usrmgt_port', 'usrmgt_magic', 'forum_secret'
    )

for opt in CONFIG_OPTIONS:
    globals()[opt] = conf[opt]

# XXX Convert db_port and usrmgt_port to int.
# Because.
db_port = int(db_port)
usrmgt_port = int(usrmgt_port)

# Additional auto-generated config options

# Path where architecture-dependent data (including non-user-executable
# binaries) is installed.
lib_path = os.path.join(prefix, 'lib/ivle')

# Path where arch-independent data is installed.
share_path = os.path.join(prefix, 'share/ivle')

# Path where user-executable binaries are installed.
bin_path = os.path.join(prefix, 'bin')

# 'site-packages' directory in Python, where Python libraries are to be
# installed.
PYTHON_VERSION = sys.version[0:3]   # eg. "2.5"
python_site_packages = os.path.join(prefix,
                           'lib/python%s/site-packages' % PYTHON_VERSION)

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

# In the local file system, where the template system jail will be stored.
jail_system_build = os.path.join(jail_src_base, '__base_build__')

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
