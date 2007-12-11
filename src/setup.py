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
# Prompts the administrator to enter machine-specific details and builds the
# file conf/conf.py.
# (This file is not included with the distribution precisely because it
# contains machine-specific settings).

import os
import sys

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

# MAIN SCRIPT

# Set up some variables

cwd = os.getcwd()
# conffile is the file that will be created/overwritten
conffile = os.path.join(cwd, "conf/conf.py")

# Fixed config options that we don't ask the admin

default_app = "dummy"

# Print the opening spiel including the GPL notice

print """IVLE - Informatics Virtual Learning Environment Setup
Copyright (C) 2007-2008 The University of Melbourne
IVLE comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions. See LICENSE.txt for details.
"""

print """IVLE Setup
This tool will create the file """ + conffile + """,
prompting you for details about your configuration. The file will be
overwritten if it already exists. It will *not* install or deploy IVLE.

Please hit Ctrl+C now if you do not wish to do this.
"""

# Get information from the administrator
# If EOF is encountered at any time during the questioning, just exit silently

root_dir = query_user("""Root directory where IVLE is located (in URL space):
(eg. "/" or "/ivle")""")
student_dir = query_user(
    """Root directory where user files are stored (on the local file system):
(eg. "/home/informatics/jails")""")

# Write conf.py

try:
    conf = open(conffile, "w")

    conf.write("""# IVLE Configuration File
# conf.py
# Miscellaneous application settings


# In URL space, where in the site is IVLE located. (All URLs will be prefixed
# with this).
# eg. "/" or "/ivle".
root_dir = """ + '"' + root_dir + '"' + """

# In the local file system, where are the student/user file spaces located.
# The user jails are expected to be located immediately in subdirectories of
# this location.
student_dir = """ + '"' + student_dir + '"' + """

# Which application to load by default (if the user navigates to the top level
# of the site). This is the app's URL name.
# Note that if this app requires authentication, the user will first be
# presented with the login screen.
default_app = """ + '"' + default_app + '"' + """
""")
    
    conf.close()
except IOError, (errno, strerror):
    print "IO error(%s): %s" % (errno, strerror)
    sys.exit(1)

print "Successfully wrote conf.py"
print
print "You may modify the configuration at any time by editing"
print conffile
print

