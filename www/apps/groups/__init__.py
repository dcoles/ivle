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

# App: groups
# Author: Matt Giuca
# Date: 21/7/2008

# Allows students and tutors to manage project groups.

from common import util

def handle(req):
    # Set request attributes
    req.content_type = "text/html"
    req.styles = ["media/groups/groups.css"]
    req.scripts = ["media/groups/groups.js"]
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Start writing data
    req.write('<div id="ivle_padding">\n')
    req.write("<p>Group Management Panel (Under Construction)</p>\n")
    req.write("</div>\n")
