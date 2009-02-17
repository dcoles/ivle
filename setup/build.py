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
    (options, args) = parser.parse_args(args)

    # Call the real function
    return __build(options.dry, options.nocompile)

def __build(dry=False, no_compile=None):
    install_list = util.InstallList()

    if dry:
        print "Dry run (no actions will be executed)\n"

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

