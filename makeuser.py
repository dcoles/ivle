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

# Program: MakeUser
# Author:  Matt Giuca
# Date:    9/1/2008

# Script to create a new user. This can also be done through the
# administration interface.
# This script wraps common.makeuser.
# It also creates a unix account which common.makeuser does not.
# (This script may not be appropriate for production on a multi-node
# environment).

import sys
import os
import os.path
import pwd
import getopt
# Import modules from the website is tricky since they're in the www
# directory.
sys.path.append(os.path.join(os.getcwd(), 'www'))
import conf
import common.makeuser, common.db

# Requireds and optionals will be used to display the usage message
# AND do argument processing
# The names here must correspond to the fields in the database.
requireds = ["login", "fullname", "rolenm"]
optionals = [
    ('p', 'password', "Cleartext password for this user"),
    ('n', 'nick', "Display name (defaults to <fullname>)"),
    ('e', 'email', "Email address"),
    ('s', 'studentid', "Student ID")
]

if len(sys.argv) <= 3:
    # Nicely format the usage message using the optionals
    print ("Usage: python makeuser.py [OPTIONS] %s\n    OPTIONS"
        % ' '.join(['<%s>' % x for x in requireds]))
    for short, long, desc in optionals:
        t = "        -%s | --%s" % (short, long)
        print t + (' ' * max(28 - len(t), 2)) + desc
    sys.exit(1)

if os.getuid() != 0:
    print "Must run makeuser.py as root."
    sys.exit(1)

shorts = ''.join([o[0] + ":" for o in optionals])
longs = [o[1] + "=" for o in optionals]
opts, args = getopt.gnu_getopt(sys.argv[1:], shorts, longs)
opts = dict(opts)

# Get the dictionary of fields from opts and args
user = {}
for i in range(0, len(requireds)):
    user[requireds[i]] = args[i]
for short, long, _ in optionals:
    try:
        user[long] = opts['-' + short]
    except KeyError:
        try:
            user[long] = opts['--' + long]
        except KeyError:
            pass
login = user['login']
if 'nick' not in user:
    user['nick'] = user['fullname']

try:
    # Resolve the user's username into a UID
    # Create the user if it does not exist
    try:
        (_,_,uid,_,_,_,_) = pwd.getpwnam(login)
    except KeyError:
        if os.system("useradd '%s'" % login) != 0:
            raise Exception("Failed to add Unix user account")
        try:
            (_,_,uid,_,_,_,_) = pwd.getpwnam(login)
        except KeyError:
            raise Exception("Failed to add Unix user account")
    user['unixid'] = uid
    # Make the user's database entry
    common.makeuser.make_user_db(**user)
except Exception, message:
    print "Error: " + str(message)
    sys.exit(1)

print "Successfully created user %s (%s)." % (login, user['fullname'])
