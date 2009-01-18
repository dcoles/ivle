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

# Module: setup/install
# Author: Matt Giuca, Refactored by David Coles
# Date:   03/07/2008

import optparse
import os
import sys

from setup import util

def install(args):
    usage = """usage: %prog install [options]
(Requires root)
Create target install directory ($target).
Create $target/bin.
Copy bin/trampoline/trampoline to $target/bin.
Copy bin/timount/timount to $target/bin.
chown and chmod the installed trampoline.
Copy www/ to $target.
Copy jail/ to jail_system directory (unless --nojail specified).
Copy subjects/ to subjects directory (unless --nosubjects specified).
"""

    # Parse arguments
    parser = optparse.OptionParser(usage)
    parser.add_option("-n", "--dry",
        action="store_true", dest="dry",
        help="Print out the actions but don't do anything.")
    parser.add_option("-J", "--nojail",
        action="store_true", dest="nojail",
        help="Don't copy jail/ to jail_system directory")
    parser.add_option("-S", "--nosubjects",
        action="store_true", dest="nosubjects",
        help="Don't copy subject/ to subjects directory.")
    (options, args) = parser.parse_args(args)

    # Call the real function
    return __install(options.dry, options.nojail, options.nosubjects)

def __install(dry=False,nojail=False,nosubjects=False):
    # We need to import the one in the working copy, not in the system path.
    confmodule = __import__("ivle/conf/conf")
    install_list = util.InstallList()

    # Pull the required varibles out of the config
    lib_path = confmodule.lib_path
    share_path = confmodule.share_path
    bin_path = confmodule.bin_path
    python_site_packages = confmodule.python_site_packages
    jail_base = confmodule.jail_base
    jail_system = confmodule.jail_system
    subjects_base = confmodule.subjects_base
    exercises_base = confmodule.exercises_base

    # Must be run as root or a dry run  
    if dry:
        print "Dry run (no actions will be executed)\n"
    
    if not dry and os.geteuid() != 0:
        print >>sys.stderr, "Must be root to run build"
        print >>sys.stderr, "(I need to chown)."
        return 1

    # Make some directories for data.
    util.action_mkdir(confmodule.log_path, dry)
    util.action_mkdir(confmodule.data_path, dry)
    util.action_mkdir(confmodule.jail_base, dry)
    util.action_mkdir(confmodule.jail_src_base, dry)
    util.action_mkdir(confmodule.content_path, dry)
    util.action_mkdir(confmodule.notices_path, dry)
    util.action_mkdir(os.path.join(confmodule.data_path, 'sessions'), dry)
    util.action_mkdir(confmodule.svn_path, dry)
    util.action_mkdir(confmodule.svn_repo_path, dry)
    util.action_mkdir(os.path.join(confmodule.svn_repo_path, 'users'), dry)
    util.action_mkdir(os.path.join(confmodule.svn_repo_path, 'groups'), dry)

    util.action_chown(confmodule.log_path, util.wwwuid, util.wwwuid, dry)
    util.action_chown(os.path.join(confmodule.data_path, 'sessions'),
                      util.wwwuid, util.wwwuid, dry)
    util.action_chown(os.path.join(confmodule.svn_repo_path, 'users'),
                      util.wwwuid, util.wwwuid, dry)
    util.action_chown(os.path.join(confmodule.svn_repo_path, 'groups'),
                      util.wwwuid, util.wwwuid, dry)

    # Create lib and copy the compiled files there
    util.action_mkdir(lib_path, dry)

    tramppath = os.path.join(lib_path, 'trampoline')
    util.action_copyfile('bin/trampoline/trampoline', tramppath, dry)
    # chown trampoline to root and set setuid bit
    util.action_chown_setuid(tramppath, dry)

    timountpath = os.path.join(lib_path, 'timount')
    util.action_copyfile('bin/timount/timount', timountpath, dry)

    # Create a services directory to put the usrmgt-server in.
    util.action_mkdir(os.path.join(share_path, 'services'), dry)

    usrmgtpath = os.path.join(share_path, 'services/usrmgt-server')
    util.action_copyfile('services/usrmgt-server', usrmgtpath, dry)
    util.action_chmod_x(usrmgtpath, dry)

    # Copy the user-executable binaries using the list.
    util.action_copylist(install_list.list_user_binaries, bin_path, dry,
                         onlybasename=True)

    # Copy the www and lib directories using the list
    util.action_copylist(install_list.list_www, share_path, dry)
    util.action_copylist(install_list.list_ivle_lib, python_site_packages, dry)
    
    # Make the config file private
    # XXX Get rid of lib
    configpath = os.path.join(python_site_packages, 'ivle/conf/conf.py')
    util.action_make_private(configpath, dry)

    # Copy the php directory
    forum_dir = "www/php/phpBB3"
    forum_path = os.path.join(share_path, forum_dir)
    util.action_copytree(forum_dir, forum_path, dry)
    print "chown -R www-data:www-data %s" % forum_path
    if not dry:
        os.system("chown -R www-data:www-data %s" % forum_path)

    if not nojail:
        # Copy the local jail directory built by the build action
        # to the jail_system directory (it will be used to help build
        # all the students' jails).
        util.action_copytree('jail', jail_system, dry)

    if not nosubjects:
        # Copy the subjects and exercises directories across
        util.action_mkdir(subjects_base, dry)
        util.action_copylist(install_list.list_subjects, subjects_base, dry,
            srcdir="./subjects")
        util.action_mkdir(exercises_base, dry)
        util.action_copylist(install_list.list_exercises, exercises_base, dry,
            srcdir="./exercises")

    # XXX We shouldn't have ivle.pth at all any more.
    # We may still need the www packages to be importable.
    # Anything from www that is needed from the outside should go to lib.
    ivle_pth = os.path.join(python_site_packages, "ivle.pth")
    try:
        file = open(ivle_pth, 'w')
        file.write(os.path.join(share_path, "www"))
        file.close()
    except (IOError, OSError):
        pass

    # Create the ivle working revision record file
    ivle_revision_record_file = os.path.join(share_path, 'ivle-revision.txt')
    if not dry:
        try:
            conf = open(ivle_revision_record_file, "w")

            conf.write("""# SVN revision r%s
# Source tree location: %s
# Modified files:
""" % (util.get_svn_revision(), os.getcwd()))

            conf.close()
        except IOError, (errno, strerror):
            print "IO error(%s): %s" % (errno, strerror)
            sys.exit(1)

        os.system("svn status . >> %s" % ivle_revision_record_file)

    print "Wrote IVLE code revision status to %s" % ivle_revision_record_file

    return 0

