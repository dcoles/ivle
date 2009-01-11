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

# Program: EnrolAllUsers
# Author:  Matt Giuca
# Date:    15/7/2008

# Script to add enrolments for all users on the system.
# Pulls from the configured subject pulldown module the subjects each student
# is enrolled in, and adds enrolments to the database.
# Does not remove any enrolments.
#
# Requires root to run.

import sys
import os
import common.db
import os.path
import pwd
import conf
import optparse
import logging

import pulldown_subj

p = optparse.OptionParser()
p.add_option('--user', '-u', metavar="<login>",
             help="Just perform enrolment for user <login>")
p.add_option('--verbose', '-v', action='store_true')
p.add_option('--year', '-y', metavar="<year>",
             help="If specified, year to make enrolments for (default: "
                  "current year)")
options, arguments = p.parse_args()

if options.verbose:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG)

if os.getuid() != 0:
    print >> sys.stderr, "%s must be run as root" % sys.argv[0]
    sys.exit(1)

try:
    db = common.db.DB()
    if options.user is None:
        users = db.get_users()
    else:
        users = [db.get_user(options.user)]
    def repack(user):
        return (user.login, user.unixid)
    uids = dict(map(repack,users))
except Exception, message:
    logging.error(str(message))
    sys.exit(1)

if options.user is None:
    logging.info("enrolment started")
else:
    logging.info("enrolment started for user %s" % options.user)

if options.year is not None and not options.year.isdigit():
    logging.error("Year must be numeric")
    sys.exit(1)

users.sort(key=lambda user: user.login)
for user in users:
    try:
        # Get all subjects this user is enrolled in, and add them to the DB if
        # they match one of our local subject codes
        res = pulldown_subj.enrol_user(user.login, options.year)
        logging.info("Enrolled user %s in %d subject%s." % (user.login, res,
                        '' if res == 1 else 's'))
    except Exception, message:
        logging.warning(str(message))
        continue
    
logging.info("enrolment completed successfully")
