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
Compiles platform-specific code, and optionally Python too.
Details:
Compiles (GCC) bin/trampoline/trampoline.c to bin/trampoline/trampoline.
Compiles (GCC) bin/timount/timount.c to bin/timount/timount.
Optionally generates .pyc files for all the IVLE .py files."""

    # Parse arguments
    parser = optparse.OptionParser(usage)
    parser.add_option("-n", "--dry",
        action="store_true", dest="dry",
        help="Print out the actions but don't do anything.")
    parser.add_option("--no-compile",
        action="store_true", dest="nocompile",
        help="Don't byte-compile .py files.")
    parser.add_option("-t", "--trampoline-uids",
        action="store", dest="tuids", default="33",
        help="Comma-separated list of UIDs allowed to use trampoline. "
             "(default: 33)")
    (options, args) = parser.parse_args(args)

    # Call the real function
    return __build(options.dry, options.nocompile, options.tuids)

def __build(dry=False, no_compile=None, tuids=None):
    install_list = util.InstallList()

    if dry:
        print "Dry run (no actions will be executed)\n"

    # Create trampoline configuration.
    conf_hfile = os.path.join(os.getcwd(), "bin/trampoline/conf.h")
    conf_h = open(conf_hfile, "w")

    conf_h.write("""/* IVLE Configuration File
 * conf.h
 * Administrator settings required by trampoline.
 * Note: trampoline will have to be rebuilt in order for changes to this file
 * to take effect.
 */

#define IVLE_AUFS_JAILS

/* Which user IDs are allowed to run the trampoline.
 * This list should be limited to the web server user.
 * (Note that root is an implicit member of this list).
 */
static const int allowed_uids[] = { %s };
""" % tuids)
    conf_h.close()

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

    # Compile .py files into .pyc or .pyo files
    if not no_compile:
        compileall.compile_dir('www', quiet=True)
        compileall.compile_dir('ivle', quiet=True)
        compileall.compile_dir('services', quiet=True)

    return 0

