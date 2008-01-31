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

# App: dummy
# Author: Matt Giuca
# Date: 12/12/2007

# This is an IVLE application.
# A sample / testing application for IVLE.

from common import util

def handle(req):
    """Handler for the Dummy application."""

    # Set request attributes
    req.content_type = "text/html"
    # These files don't really exist - just a test of our linking
    # capabilities
    req.styles = ["media/dummy/dummy.css"]
    req.scripts = ["media/dummy/dummy.js", "media/dummy/hello.js"]
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Start writing data
    req.write('<div id="ivle_padding">\n')
    req.write("<p>Hello, IVLE!</p>\n")
    req.write('<p>')
    if req.app == None:
        req.write('<b>No app specified</b>')
    else:
        req.write('<b>' + req.app + '</b> ')
        req.write('<img src="' + util.make_path("media/images/mime/dir.png")
            + '" /> ')
        req.write(str(req.path))
    req.write("</p>\n")
    req.write("</div>\n")
