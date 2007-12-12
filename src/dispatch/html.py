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

# Module: dispatch.html
# Author: Matt Giuca
# Date: 12/12/2007

# Provides functions for writing the dispatch-generated HTML header and footer
# content (the common parts of the HTML pages shared across the entire site).
# Does not include the login page. See login.py.

def write_html_head(req):
    """Writes the HTML header, given a request object.

    req: An IVLE request object. Reads attributes such as title. Also used to
    write to."""
    # TODO: Full header
    req.write("<html>\n<body>\n")

def write_html_foot(req):
    """Writes the HTML footer, given a request object.

    req: An IVLE request object. Written to.
    """
    req.write("</body>\n</html>\n")
