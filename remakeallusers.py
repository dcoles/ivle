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
import optparse
import shutil
import logging

p = optparse.OptionParser()
p.add_option('--incremental', '-i', action='store_true')
p.add_option('--verbose', '-v', action='store_true')
options, arguments = p.parse_args()

if options.verbose:
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.DEBUG)

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

# First check that our __templateuser__ directory exits, if not create it
templateuserdir = os.path.join(conf.jail_base, '__templateuser__')
stagingdir = templatedir = os.path.join(conf.jail_base, '__staging__')
if not os.path.isdir(templateuserdir):
    os.mkdir(templateuserdir)

# Generate manifest of files that differ between template user and staging
if options.incremental:
    logging.info("incremental rebuild started")
    manifest = common.makeuser.generate_manifest(stagingdir, templateuserdir)
    logging.debug("generated change manifest")
    logging.debug("  adding/updating: %s" % manifest[0])
    logging.debug("  removing: %s" % manifest[1])
else:
    # Force a full rebuild
    logging.info("full rebuild started")
    manifest = None

list.sort(key=lambda user: user.login)
for user in list:
    login = user.login

    try:
        # Resolve the user's login into a UID
        # Create the user if it does not exist
        try:
            uid = uids[login]
        except KeyError:
            raise Exception("user %s does not have a unixid in the database"
                % login)
        # Remake the user's jail
        common.makeuser.make_jail(login, uid, manifest=manifest)
    except Exception, message:
        logging.warning(str(message))
        continue

    logging.debug("recreated user %s's jail." % login)
    
# Update the template user directory
logging.debug("updating templateuser directory")
shutil.rmtree(templateuserdir)
#common.makeuser.linktree(stagingdir, templateuserdir)
common.makeuser.make_jail('__templateuser__', 0, manifest=manifest)
shutil.rmtree(os.path.join(templateuserdir, 'home'))

logging.info("rebuild completed successfully")
