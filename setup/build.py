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

# Module: setup/build
# Author: Matt Giuca, Refactored by David Coles
# Date:   02/07/2008

import optparse
import os
import sys
import compileall

from setup import util

def build(args):
    usage = """usage: %prog build [options]
(requires root)
Compiles all files and sets up a jail template in the source directory.
-O is recommended to cause compilation to be optimised.
Details:
Compiles (GCC) bin/trampoline/trampoline.c to bin/trampoline/trampoline.
Compiles (GCC) bin/timount/timount.c to bin/timount/timount.
Creates jail with system and student packages installed from MIRROR.
Copies console/ to a location within the jail.
Copies OS programs and files to corresponding locations within the jail
  (eg. python and Python libs, ld.so, etc).
Generates .pyc or .pyo files for all the IVLE .py files."""

    # Parse arguments
    parser = optparse.OptionParser(usage)
    parser.add_option("-n", "--dry",
        action="store_true", dest="dry",
        help="Print out the actions but don't do anything.")
    parser.add_option("-j", "--rebuildjail",
        action="store_true", dest="rebuildjail",
        help="Don't recreate jail/ - just update its IVLE code.")
    parser.add_option("-m", "--mirror",
        action="store", dest="apt_mirror",
        help="Sets the APT mirror used to build the jail.")
    (options, args) = parser.parse_args(args)

    # Call the real function
    return __build(options.dry, options.rebuildjail, options.apt_mirror)

def __build(dry=False,rebuildjail=False,apt_mirror=None):
    # We need to import the one in the working copy, not in the system path.
    confmodule = __import__("ivle/conf/conf")
    install_list = util.InstallList()

    # Must be run as root or a dry run  
    if dry:
        print "Dry run (no actions will be executed)\n"
    
    if not dry and os.geteuid() != 0:
        print >>sys.stderr, "Must be root to run build"
        print >>sys.stderr, "(I need to chroot)."
        return 1
    
    if not rebuildjail and not os.path.exists('jail'):
        print >> sys.stderr, "No jail exists -- please rerun with -j."
        return 1

    # Compile the trampoline
    curdir = os.getcwd()
    os.chdir('bin/trampoline')
    util.action_runprog('make', [], dry)
    os.chdir(curdir)

    # Compile timount
    curdir = os.getcwd()
    os.chdir('bin/timount')
    util.action_runprog('make', [], dry)
    os.chdir(curdir)

    if rebuildjail:
        # Create the jail and its subdirectories
        # Note: Other subdirs will be made by copying files
        if apt_mirror != None:
            os.environ['MIRROR'] = apt_mirror
        util.action_runprog('setup/buildjail.sh', [], dry)

    # Copy all console and operating system files into the jail
    jail_share = os.path.join('jail', confmodule.share_path[1:])
    jail_services = os.path.join(jail_share, 'services')
    util.action_copylist(install_list.list_services, jail_share, dry)

    # Chmod the python console
    util.action_chmod_x(os.path.join(jail_services, 'python-console'), dry)
    util.action_chmod_x(os.path.join(jail_services, 'fileservice'), dry)
    util.action_chmod_x(os.path.join(jail_services, 'serveservice'), dry)

    # Also copy the IVLE lib directory into the jail
    # This is necessary for running certain services
    jail_site_packages = os.path.join('jail',
                                      confmodule.python_site_packages[1:])
    util.action_copylist(install_list.list_ivle_lib, jail_site_packages, dry)
    # IMPORTANT: ivle/conf/conf.py contains details
    # which could compromise security if left in the jail (such as the DB
    # password).
    # The "safe" version is in jailconf.py. Delete conf.py and replace it with
    # jailconf.py.
    util.action_copyfile('ivle/conf/jailconf.py',
        os.path.join(jail_site_packages, 'ivle/conf/conf.py'), dry)

    # Compile .py files into .pyc or .pyo files
    compileall.compile_dir('www', quiet=True)
    compileall.compile_dir('ivle', quiet=True)
    compileall.compile_dir('services', quiet=True)
    compileall.compile_dir(os.path.join(jail_site_packages, 'ivle'),quiet=True)

    return 0

