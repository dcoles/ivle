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

# Program: RemakeAllUsers
# Author:  Matt Giuca
# Date:    3/3/2008

# Script to rebuild jails for all users on the system.
# Requires root to run.

import sys
import os
import common.db
import os.path
import pwd
import conf
import common.makeuser
# Import modules from the website is tricky since they're in the www
# directory.
sys.path.append(os.path.join(os.getcwd(), 'www'))

if os.getuid() != 0:
    print "Must run remakeallusers.py as root."
    sys.exit()

try:
    db = common.db.DB()
    list = db.get_users()
except Exception, message:
    print "Error: " + str(message)
    sys.exit(1)

list.sort(key=lambda user: user.login)
for user in list:
    username = user.login

    try:
        # Resolve the user's username into a UID
        # Create the user if it does not exist
        try:
            (_,_,uid,_,_,_,_) = pwd.getpwnam(username)
        except KeyError:
            raise Exception("User %s does not have a Unix user account"
                % username)
        # Remake the user's jail
        common.makeuser.make_jail(username, uid)
    except Exception, message:
        print "Error: " + str(message)
        continue

    print "Successfully recreated user %s's jail." % username
