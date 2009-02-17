# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
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

# Module: parse_exercise
# Author: Dilshan Angampitiya
#         Steven Bird (revisions)

"""
This file was hacked apart by Nick
"""

from TestFramework import *

def parse_exercise_file(exercise, console):
    """ Parse an xml exercise file and return a testsuite for that exercise """
    # Generate the TestSuite for the given exercise
    return TestSuite(exercise, console)

