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

# Module: setup
# Author: Matt Giuca
# Date:   12/12/2007

# This is a command-line application, for use by the administrator.
# This program is a frontend for the modules in the setup packages that 
# build and install IVLE in separate steps.
# It is called with at least one argument, which specifies which operation to
# take.

import sys
import setup.build
import setup.install

def main(argv=None):
    if argv is None:
        argv = sys.argv

    # Print the opening spiel including the GPL notice

    print """IVLE - Informatics Virtual Learning Environment Setup
Copyright (C) 2007-2009 The University of Melbourne
IVLE comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions. See LICENSE.txt for details.

IVLE Setup
"""

    # First argument is the name of the setup operation
    try:
        operation = argv[1]
    except IndexError:
        # Print usage message and exit
        help([])
        return 1

    oper_func = call_operator(operation)
    return oper_func(argv[2:])

def help(args):
    if len(args)!=1:
        print """Usage: python setup.py operation [options]
Operation can be:
    help [operation]
    build
    install

    For help and options for a specific operation use 'help [operation]'."""
    else:
        operator = args[0]
        oper_func = call_operator(operator)
        oper_func(['operator','--help'])

def call_operator(operation):
    # Call the requested operation's function
    try:
        oper_func = {
            'help' : help,
            'build' : setup.build.build,
            'install' : setup.install.install,
        }[operation]
    except KeyError:
        print >>sys.stderr, (
            """Invalid operation '%s'. Try python setup.py help."""
            % operation)
        sys.exit(1)
    return oper_func

if __name__ == "__main__":
    sys.exit(main())

