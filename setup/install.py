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
import functools

from setup import util

PYTHON_VERSION = sys.version[:3]

def install(args):
    usage = """usage: %prog install [options]
(Requires root)
Create target install directory ($target).
Create $target/bin.
Copy bin/trampoline/trampoline to $target/bin.
Copy bin/timount/timount to $target/bin.
Copy etc/ivle.conf to /etc/ivle/ivle.conf.
chown and chmod the installed trampoline.
Copy www/ to $target.
"""

    # Parse arguments
    parser = optparse.OptionParser(usage)
    parser.add_option("-n", "--dry",
        action="store_true", dest="dry",
        help="Print out the actions but don't do anything.")
    parser.add_option("-R", "--nosvnrevno",
        action="store_true", dest="nosvnrevno",
        help="Don't write out the Subversion revision to the share directory.")
    parser.add_option("--root",
        action="store", dest="rootdir",
        help="Install into a different root directory.",
        default='/')
    parser.add_option("--prefix",
        action="store", dest="prefix",
        help="Base prefix to install IVLE into (default: /usr/local).",
        default='/usr/local')
    parser.add_option("--python-site-packages",
        action="store", dest="python_site_packages",
        help="Path to Python site packages directory.",
        default='/usr/local/lib/python%s/site-packages' % PYTHON_VERSION)
    (options, args) = parser.parse_args(args)

    # Call the real function
    return __install(prefix=options.prefix,
                     python_site_packages=options.python_site_packages,
                     dry=options.dry, rootdir=options.rootdir,
                     nosvnrevno=options.nosvnrevno)

def __install(prefix, python_site_packages, dry=False, rootdir=None,
              nosvnrevno=False):
    install_list = util.InstallList()

    # We need to apply make_install_path with the rootdir to an awful lot of
    # config variables, so make it easy:
    mip = functools.partial(util.make_install_path, rootdir)

    # Compute the lib_path, share_path and bin_path (copied from
    # ivle/conf/conf.py).
    lib_path = mip(os.path.join(prefix, 'lib/ivle'))
    share_path = mip(os.path.join(prefix, 'share/ivle'))
    bin_path = mip(os.path.join(prefix, 'bin'))
    python_site_packages = mip(python_site_packages)

    # Must be run as root or a dry run  
    if dry:
        print "Dry run (no actions will be executed)\n"
    
    if not dry and os.geteuid() != 0:
        print >>sys.stderr, "Must be root to run install"
        return 1

    # Create the config directory.
    util.action_mkdir('/etc/ivle', dry)

    # Create lib and copy the compiled files there
    util.action_mkdir(lib_path, dry)

    tramppath = os.path.join(lib_path, 'trampoline')
    util.action_copyfile('bin/trampoline/trampoline', tramppath, dry)
    # chown trampoline to root and set setuid bit
    util.action_chown_setuid(tramppath, dry)

    timountpath = os.path.join(lib_path, 'timount')
    util.action_copyfile('bin/timount/timount', timountpath, dry)

    # Copy in the services (only usrmgt-server is needed on the host, but
    # the jail build requires the rest).
    util.action_copylist(install_list.list_services, share_path, dry)
    usrmgtpath = os.path.join(share_path, 'services/usrmgt-server')
    util.action_chmod_x(usrmgtpath, dry)

    # Copy the user-executable binaries using the list.
    util.action_copylist(install_list.list_user_binaries, bin_path, dry,
                         onlybasename=True)

    # Copy the www directory (using the list)
    util.action_copylist(install_list.list_www, share_path, dry)

    # Set appropriate permissions on the php directory
    forum_dir = "www/php/phpBB3"
    forum_path = os.path.join(share_path, forum_dir)
    print "chown -R www-data:www-data %s" % forum_path
    if not dry:
        os.system("chown -R www-data:www-data %s" % forum_path)

    # Copy the lib directory (using the list)
    util.action_copylist(install_list.list_ivle_lib, python_site_packages, dry)

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

    if not nosvnrevno:
        # Create the ivle working revision record file
        ivle_revision_file = os.path.join(share_path, 'revision.txt')
        if not dry:
            try:
                conf = open(ivle_revision_file, "w")

                conf.write("""# SVN revision r%s
# Source tree location: %s
# Modified files:
""" % (util.get_svn_revision(), os.getcwd()))

                conf.close()
            except IOError, (errno, strerror):
                print "IO error(%s): %s" % (errno, strerror)
                sys.exit(1)

            os.system("svn status . >> %s" % ivle_revision_file)

        print "Wrote IVLE code revision status to %s" % ivle_revision_file

    return 0

