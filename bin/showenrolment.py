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

# Program: showenrolment
# Author:  William Grant
# Date:    08/08/2008

# Script to show a user's enrolments.

import common.db

import sys

if len(sys.argv) != 2:
    print >> sys.stderr, "usage: %s <login>" % sys.argv[0]
    sys.exit(1)

db = common.db.DB()
try:
    user = db.get_user(sys.argv[1])
except common.db.DBException:
    print >> sys.stderr, "cannot retrieve user - probably doesn't exist"
    sys.exit(1)
enrols = db.get_enrolment(sys.argv[1])
db.close()

if len(enrols) > 0:
    print 'Showing enrolment for %s (%s):' % (sys.argv[1], user.fullname)
    print '    Code       Name Semester Year'
    print '-------- ---------- -------- ----'
    for enrol in enrols:
        print '%(subj_code)8s %(subj_short_name)10s %(semester)8s %(year)4s' % enrol
else:
    print '%s (%s) is not enrolled in any offerings' % (sys.argv[1], user.fullname)
