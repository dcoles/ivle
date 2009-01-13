# IVLE
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

# App: tos
# Author: Matt Giuca
# Date: 14/2/2008

# Terms of Service app
# Displays the TOS
# (Mostly this is here for the "Help" section)

import os

from ivle import util

def handle(req):
    """Handler for the TOS application."""

    # Set request attributes
    req.content_type = "text/html"
    req.write_html_head_foot = True

    # Start writing data
    req.write("""<div id="ivle_padding">
<p>When you first logged into IVLE, you agreed to the following Terms of
Service:</p>
<hr />
""")

    # Print out the contents of the license file
    util.send_terms_of_service(req)
    req.write('<hr />\n</div>\n')
