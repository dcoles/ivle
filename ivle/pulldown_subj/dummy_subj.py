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

# Module: Dummy Subject Pulldown Module
# Author: Matt Giuca
# Date:   7/7/2008

# Pluggable subject pulldown module - dummy.
# Acts as a demonstration subject pulldown module.
# Don't actually use this - it reports bogus subjects.

def get_subjects(login):
    """
    All subject pulldown modules must have a get_subjects(login)
    function, such as this.
    Returns a list of (subject, semester) pairs for all subjects this student
    is enrolled in.
    """
    if ord(login[:1]) < ord('m'):
        # Return a list of subject/semester pairs
        return [
            (u'12345', u'1'),
            (u'12345', u'2'),
            (u'98765', u'1'),
        ]
    else:
        # This demonstrates that you can return None, to indicate to the
        # system to use a different pulldown method.
        return None
