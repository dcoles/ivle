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
import compileall
from setuputil import *

def build(args):
    usage = """usage: %prog build [options]
(requires root)
Compiles all files and sets up a jail template in the source directory.
-O is recommended to cause compilation to be optimised.
Details:
Compiles (GCC) trampoline/trampoline.c to trampoline/trampoline.
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
    parser.add_option("-m", "--mirror",
        action="store", dest="apt_mirror",
        help="Sets the APT mirror used to build the jail.")
    (options, args) = parser.parse_args(args)

    # Call the real function
    __build(options.dry, options.apt_mirror)

def __build(dry=False,apt_mirror=None):
    # Importing configuration is a little tricky
    sys.path.append(os.pardir)
    import install_list

    # Must be run as root or a dry run  
    if dry:
        print "Dry run (no actions will be executed)\n"
    
    if not dry and os.geteuid() != 0:
        print >>sys.stderr, "Must be root to run build"
        print >>sys.stderr, "(I need to chroot)."
        return 1
    
    # Find out the revison number
    revnum = get_svn_revision()
    print "Building Revision %s"%str(revnum)
    if not dry:
        vfile = open('BUILD-VERSION','w')
        vfile.write(str(revnum) + '\n')
        vfile.close()

    # Compile the trampoline
    curdir = os.getcwd()
    os.chdir('trampoline')
    action_runprog('make', [], dry)
    os.chdir(curdir)

    # Create the jail and its subdirectories
    # Note: Other subdirs will be made by copying files
    if apt_mirror != None:
        os.environ['MIRROR'] = apt_mirror
    action_runprog('./buildjail.sh', [], dry)

    # Copy all console and operating system files into the jail
    action_copylist(install_list.list_scripts, 'jail/opt/ivle', dry)
    
    # Chmod the python console
    action_chmod_x('jail/opt/ivle/scripts/python-console', dry)
    action_chmod_x('jail/opt/ivle/scripts/fileservice', dry)
    action_chmod_x('jail/opt/ivle/scripts/serveservice', dry)
    
    # Also copy the IVLE lib directory into the jail
    # This is necessary for running certain scripts
    action_copylist(install_list.list_lib, 'jail/opt/ivle', dry)
    # IMPORTANT: The file jail/opt/ivle/lib/conf/conf.py contains details
    # which could compromise security if left in the jail (such as the DB
    # password).
    # The "safe" version is in jailconf.py. Delete conf.py and replace it with
    # jailconf.py.
    action_copyfile('lib/conf/jailconf.py',
        'jail/opt/ivle/lib/conf/conf.py', dry)

    # Compile .py files into .pyc or .pyo files
    compileall.compile_dir('www', quiet=True)
    compileall.compile_dir('lib', quiet=True)
    compileall.compile_dir('scripts', quiet=True)
    compileall.compile_dir('jail/opt/ivle/lib', quiet=True)

    # Set up ivle.pth inside the jail
    # Need to set /opt/ivle/lib to be on the import path
    ivle_pth = \
        "jail/usr/lib/python%s/site-packages/ivle.pth" % PYTHON_VERSION
    f = open(ivle_pth, 'w')
    f.write('/opt/ivle/lib\n')
    f.close()

    return 0

