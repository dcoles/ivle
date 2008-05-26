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
# Import modules from the website is tricky since they're in the www
# directory.
sys.path.append(os.path.join(os.getcwd(), 'www'))

p = optparse.OptionParser()
p.add_option('--incremental', '-i', action='store_true')
options, arguments = p.parse_args()

if os.getuid() != 0:
    print "Must run remakeallusers.py as root."
    sys.exit()

try:
    db = common.db.DB()
    list = db.get_users()
    res = db.get_all('login', ['login', 'unixid'])
    def repack(flds):
        return (flds['login'], flds['unixid'])
    uids = dict(map(repack,res))

except Exception, message:
    print "Error: " + str(message)
    sys.exit(1)

# First check that our __templateuser__ directory exits, if not create it
templateuserdir = os.path.join(conf.jail_base, '__templateuser__')
stagingdir = templatedir = os.path.join(conf.jail_base, '__staging__')
if not os.path.isdir(templateuserdir):
    os.mkdir(templateuserdir)

# Generate manifest of files that differ between template user and staging
if options.incremental:
    print "Incremental Rebuild selected"
    manifest = common.makeuser.generate_manifest(stagingdir, templateuserdir)
    print "Generated change manifest"
    print "Adding/Updating: %s\nRemoving: %s" % manifest
else:
    # Force a full rebuild
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
            raise Exception("User %s does not have a unixid in the database"
                % login)
        # Remake the user's jail
        common.makeuser.make_jail(login, uid, manifest=manifest)
    except Exception, message:
        print "Error: " + str(message)
        continue

    print "Successfully recreated user %s's jail." % login
    
# Update the template user directory
print "Updating templateuser directory"
shutil.rmtree(templateuserdir)
#common.makeuser.linktree(stagingdir, templateuserdir)
common.makeuser.make_jail('__templateuser__', 0, manifest=manifest)
shutil.rmtree(os.path.join(templateuserdir, 'home'))

print "Done!"
