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
# Import modules from the website is tricky since they're in the www
# directory.
sys.path.append(os.path.join(os.getcwd(), 'www'))
import conf
import common.makeuser

if len(sys.argv) <= 6:
    print "Usage: python makeuser.py <username> <password> <nick> " \
        "<fullname> <rolenm> <studentid>"
    sys.exit()

if os.getuid() != 0:
    print "Must run makeuser.py as root."
    sys.exit()

username = sys.argv[1]
password = sys.argv[2]
nick = sys.argv[3]
fullname = sys.argv[4]
rolenm = sys.argv[5]
studentid = sys.argv[6]

try:
    # Resolve the user's username into a UID
    # Create the user if it does not exist
    try:
        (_,_,uid,_,_,_,_) = pwd.getpwnam(username)
    except KeyError:
        if os.system("useradd '%s'" % username) != 0:
            raise Exception("Failed to add Unix user account")
        try:
            (_,_,uid,_,_,_,_) = pwd.getpwnam(username)
        except KeyError:
            raise Exception("Failed to add Unix user account")
    # Make the user's jail
    common.makeuser.make_jail(username, uid)
    # Make the user's database entry
    common.makeuser.make_user_db(username, uid, password, nick, fullname,
        rolenm, studentid)
except Exception, message:
    print "Error: " + str(message)
    sys.exit(1)

print "Successfully created user %s (%s)." % (username, fullname)
