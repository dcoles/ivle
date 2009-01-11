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

# Script to rebuild jails for users on the system.
# One can specify a single username, or that all should be rebuilt.
# Requires root to run.

import sys
import os
import common.db
import common.makeuser
import optparse
import logging

p = optparse.OptionParser()
p.add_option('--verbose', '-v', action='store_true')
p.add_option('--all', '-a', action='store_true')
options, arguments = p.parse_args()

level = logging.DEBUG if options.verbose else logging.WARNING

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=level)


if os.getuid() != 0:
    print >> sys.stderr, "%s must be run as root" % sys.argv[0]
    sys.exit(1)

try:
    db = common.db.DB()
    if options.all:
        list = db.get_users()
    else:
        if len(arguments) == 0:
            print >> sys.stderr, "must be run with -a or a username"
            sys.exit(1)
        list = [db.get_user(arguments[0])]
    res = db.get_all('login', ['login', 'unixid'])
    def repack(flds):
        return (flds['login'], flds['unixid'])
    uids = dict(map(repack,res))
except Exception, message:
    logging.error(str(message))
    sys.exit(1)

logging.info("rebuild started")

list.sort(key=lambda user: user.login)
for user in list:
    login = user.login

    try:
        # Resolve the user's login into a UID
        try:
            uid = uids[login]
        except KeyError:
            raise Exception("user %s does not have a unixid in the database"
                % login)
        # Remake the user's jail
        common.makeuser.make_jail(login, uid)
    except Exception, message:
        logging.warning(str(message))
        continue

    logging.debug("recreated user %s's jail." % login)
    
logging.info("rebuild completed successfully")
