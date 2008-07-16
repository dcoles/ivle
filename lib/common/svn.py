# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2008 The University of Melbourne
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

# Module: Subversion utilities
# Author: William Grant
# Date:   16/07/2008

import pysvn

def revision_from_string(r_str):
    if r_str is None:
        pass
    elif r_str == "HEAD":
        return pysvn.Revision( pysvn.opt_revision_kind.head )
    elif r_str == "WORKING":
        return pysvn.Revision( pysvn.opt_revision_kind.working )
    elif r_str == "BASE":
        return pysvn.Revision( pysvn.opt_revision_kind.base )
    else:
        # Is it a number?
        try:
            r = int(r_str)
            return pysvn.Revision( pysvn.opt_revision_kind.number, r)
        except:
            pass
    return None
