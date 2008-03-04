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

# Program: RemakeUser
# Author:  Matt Giuca
# Date:    5/2/2008

# Repairs a user's jail, without actually writing to the DB.
# (This asks for less input than makeuser).
# This script wraps common.makeuser.

import sys
import os
import os.path
import pwd
# Import modules from the website is tricky since they're in the www
# directory.
sys.path.append(os.path.join(os.getcwd(), 'www'))
import conf
import common.makeuser
import common.db

if len(sys.argv) <= 1:
    print "Usage: python remakeuser.py <login>"
    sys.exit()

if os.getuid() != 0:
    print "Must run remakeuser.py as root."
    sys.exit()

login = sys.argv[1]

try:
    # Resolve the user's login into a UID
    # Create the user if it does not exist
    try:
        conn = common.db.DB()
        uid = conn.get_single({'login':login}, 'login', ['unixid'], ['login'])
    except KeyError:
        raise Exception("User does not have a unixid in the database")
    # Remake the user's jail
    common.makeuser.make_jail(login, uid)
except Exception, message:
    print "Error: " + str(message)
    sys.exit(1)

print "Successfully recreated user %s's jail." % login
