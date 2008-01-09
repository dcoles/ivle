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

import sys
import os
import os.path
# Import modules from the website is tricky since they're in the www
# directory.
sys.path.append(os.path.join(os.getcwd(), 'www'))
import conf
import common.makeuser

if len(sys.argv) <= 1:
    print "Usage: python makeuser.py <username>"
    sys.exit()

username = sys.argv[1]

try:
    common.makeuser.makeuser(username)
except Exception, message:
    print "Error: " + str(message)
    sys.exit(1)

print "Successfully created user " + username + "."