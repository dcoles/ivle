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

# Program: MountAllUsers
# Author:  William Grant
# Date:    4/7/2008

# Script to UnionFS-mount jails for all users on the system.
# Requires root to run.

import sys
import os
import common.db
import os.path
import conf
import optparse
import logging

p = optparse.OptionParser()
p.add_option('--verbose', '-v', action='store_true')
p.add_option('--unmount', '-u', action='store_true')
options, arguments = p.parse_args()

if options.verbose:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG)
else:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.WARNING)

if os.getuid() != 0:
    print >> sys.stderr, "%s must be run as root" % sys.argv[0]
    sys.exit(1)

try:
    db = common.db.DB()
    list = db.get_users()
    res = db.get_all('login', ['login', 'unixid'])
    def repack(flds):
        return (flds['login'], flds['unixid'])
    uids = dict(map(repack,res))
except Exception, message:
    logging.error(str(message))
    sys.exit(1)

logging.info("mass aufs mount started")

list.sort(key=lambda user: user.login)
for user in list:
    login = user.login
    # This is where we'll mount to...
    destdir = os.path.join(conf.jail_base, login)
    # ... and this is where we'll get the user bits.
    srcdir = os.path.join(conf.jail_src_base, login)

    try:
        if not options.unmount:
            if not os.path.exists(srcdir):
                logging.info("user %s doesn't have a jail - skipping" % login)
                continue
            if not os.path.exists(destdir):
                logging.debug("user %s had no mountpoint - creating" % login)
                os.mkdir(destdir)
	
            if os.system('/bin/mount -t aufs -o dirs=%s:%s=ro none %s'
                             % (srcdir,conf.jail_system,destdir)) == 0:
                logging.info("mounted user %s's jail." % login)
            else:
                logging.error("failed to mount user %s's jail!" % login)
        else:
            os.system('/bin/umount ' + destdir)
            logging.info("unmounted user %s's jail." % login)
    except Exception, message:
        logging.warning(str(message))
        continue

logging.info("mount completed successfully")