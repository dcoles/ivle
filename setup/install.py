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

# setup/build.py
# Compiles all files and sets up a jail template in the source directory.
# Details:
# Compiles (GCC) trampoline/trampoline.c to trampoline/trampoline.
# Creates jail/.
# Creates standard subdirs inside the jail, eg bin, opt, home, tmp.
# Copies console/ to a location within the jail.
# Copies OS programs and files to corresponding locations within the jail
#   (eg. python and Python libs, ld.so, etc).
# Generates .pyc files for all the IVLE .py files.

import optparse
import os
from setuputil import *

def install(args):
    usage = """usage: %prog install [options]
(Requires root)
Create target install directory ($target).
Create $target/bin.
Copy trampoline/trampoline to $target/bin.
Copy timount/timount to $target/bin.
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
    __install(options.dry, options.nojail, options.nosubjects)

def __install(dry=False,nojail=False,nosubjects=False):
    # Importing configuration is a little tricky
    sys.path.append('lib')
    import conf.conf
    import install_list

    # Pull the required varibles out of the config
    ivle_install_dir = conf.conf.ivle_install_dir
    jail_base = conf.conf.jail_base
    jail_system = conf.conf.jail_system
    subjects_base = conf.conf.subjects_base
    exercises_base = conf.conf.exercises_base

    # Must be run as root or a dry run  
    if dry:
        print "Dry run (no actions will be executed)\n"
    
    if not dry and os.geteuid() != 0:
        print >>sys.stderr, "Must be root to run build"
        print >>sys.stderr, "(I need to chown)."
        return 1
    
    # Create the target (install) directory
    action_mkdir(ivle_install_dir, dry)

    # Create bin and copy the compiled files there
    action_mkdir(os.path.join(ivle_install_dir, 'bin'), dry)
    tramppath = os.path.join(ivle_install_dir, 'bin/trampoline')
    action_copyfile('trampoline/trampoline', tramppath, dry)
    # chown trampoline to root and set setuid bit
    action_chown_setuid(tramppath, dry)

    timountpath = os.path.join(ivle_install_dir, 'bin/timount')
    action_copyfile('timount/timount', timountpath, dry)

    # Create a scripts directory to put the usrmgt-server in.
    action_mkdir(os.path.join(ivle_install_dir, 'scripts'), dry)
    usrmgtpath = os.path.join(ivle_install_dir, 'scripts/usrmgt-server')
    action_copyfile('scripts/usrmgt-server', usrmgtpath, dry)
    action_chmod_x(usrmgtpath, dry)

    # Copy the www and lib directories using the list
    action_copylist(install_list.list_www, ivle_install_dir, dry)
    action_copylist(install_list.list_lib, ivle_install_dir, dry)
    
    # Make the config file private
    configpath = os.path.join(ivle_install_dir, 'lib/conf/conf.py')
    action_make_private(configpath, dry)

    # Copy the php directory
    forum_dir = "www/php/phpBB3"
    forum_path = os.path.join(ivle_install_dir, forum_dir)
    action_copytree(forum_dir, forum_path, dry)
    print "chown -R www-data:www-data %s" % forum_path
    if not dry:
        os.system("chown -R www-data:www-data %s" % forum_path)

    if not nojail:
        # Copy the local jail directory built by the build action
        # to the jail_system directory (it will be used to help build
        # all the students' jails).
        action_copytree('jail', jail_system, dry)
    if not nosubjects:
        # Copy the subjects and exercises directories across
        action_copylist(install_list.list_subjects, subjects_base, dry,
            srcdir="./subjects")
        action_copylist(install_list.list_exercises, exercises_base, dry,
            srcdir="./exercises")

    # Append IVLE path to ivle.pth in python site packages
    # (Unless it's already there)
    ivle_pth = os.path.join(sys.prefix,
        "lib/python%s/site-packages/ivle.pth" % PYTHON_VERSION)
    ivle_www = os.path.join(ivle_install_dir, "www")
    ivle_lib = os.path.join(ivle_install_dir, "lib")
    write_ivle_pth = True
    write_ivle_lib_pth = True
    try:
        file = open(ivle_pth, 'r')
        for line in file:
            if line.strip() == ivle_www:
                write_ivle_pth = False
            elif line.strip() == ivle_lib:
                write_ivle_lib_pth = False
        file.close()
    except (IOError, OSError):
        pass
    if write_ivle_pth:
        action_append(ivle_pth, ivle_www)
    if write_ivle_lib_pth:
        action_append(ivle_pth, ivle_lib)


    # Create the ivle working revision record file
    action_mkdir(os.path.join(ivle_install_dir, 'version'), dry)
    ivle_revision_record_file = os.path.join(ivle_install_dir, 'version/ivle-revision.txt')
    if not dry:
        try:
            conf = open(ivle_revision_record_file, "w")

            conf.write( "# IVLE code revision listing generated by running 'svn status -v ..' from " + os.getcwd() + "\n#\n\n")

            conf.close()
        except IOError, (errno, strerror):
            print "IO error(%s): %s" % (errno, strerror)
            sys.exit(1)

        os.system("svn status -v . >> %s" % ivle_revision_record_file)

    print "Wrote IVLE code revision status to %s" % ivle_revision_record_file

    return 0

