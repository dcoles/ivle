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

# Program: ListUsers
# Author:  Matt Giuca
# Date:    6/2/2008

# Script to list all users on the system.
# Requires root to run.

import sys
import os
import common.db

if os.getuid() != 0:
    print "Must run listusers.py as root."
    sys.exit()

try:
    db = common.db.DB()
    list = db.get_users()
except Exception, message:
    print "Error: " + str(message)
    sys.exit(1)

for user in list:
    print repr((user['login'], user['state'], user['unixid'], user['email'],
        user['nick'], user['fullname'], user['rolenm'], user['studentid']))
