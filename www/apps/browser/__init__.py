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

# App: File Browser
# Author: Matt Giuca
# Date: 9/1/2008

# The file browser application. Presents an Ajax-based interface to the
# student's subversion workspace.
# Note that there is virtually no server-side code for this application. It
# simply presents static HTML and JavaScript, and all server-side activities
# take place in the FileService app (for handling Ajax requests).

import os.path
import cgi

from common import util

# url path for this app
THIS_APP = "files"

def handle(req):
    """Handler for the File Browser application."""

    # Work out where we are browsing
    browsepath = req.path
    if len(browsepath) == 0:
        # If no path specified, default to the user's home directory
        browsepath = req.user.login

    # Set request attributes
    req.content_type = "text/html"
    req.styles = [
        "media/browser/browser.css",
        "media/browser/listing.css",
        "media/browser/editor.css",
    ]
    req.scripts = [
        "media/common/json2.js",
        "media/common/edit_area/edit_area_full.js",
        "media/common/util.js",
        "media/browser/browser.js",
        "media/browser/listing.js",
        "media/browser/editor.js",
    ]
    req.write_html_head_foot = True     # Have dispatch print head and foot
    # The page title should contain the name of the file being browsed
    req.title = browsepath.rsplit('/', 1)[-1]

    # Start writing data
    req.write("""
<!-- Top bar section -->

<div id="topbar">
  <div id="path">
    """)
    # TODO: Work out if this is a directory or not
    presentpath(req, browsepath, True)
    req.write("""
  </div>
  <div id="actions1"></div>
  <div id="actions2"></div>
</div>
<!-- End topbar -->

<!-- Body. The JavaScript places content here relevant to the path -->
<div id="filesbody">
</div>
<!-- End body -->

</body>
</html>
""")

def presentpath(req, path, isdir):
    """
    Presents a path list (address bar inside the page) for clicking.
    Writes to req, expecting to have just written the opening div containing
    the listing.
    """
    href_path = util.make_path(THIS_APP)
    nav_path = ""

    # Create all of the paths
    pathlist = path.split("/")
    segs_left = len(pathlist)
    for path_seg in pathlist:
        if path_seg == "":
            continue
        # Write a slash at the end unless this is the last path seg AND
        # it's not a directory.
        segs_left -= 1
        add_slash = segs_left != 0 or isdir
        # Make an 'a' element
        href_path = href_path + '/' + path_seg
        nav_path = nav_path + path_seg
        if add_slash:
            nav_path = nav_path + '/'
        link = '<a href="%s" title="Navigate to %s">%s</a>' % (
            href_path, nav_path, path_seg)
        req.write(link)
        if add_slash:
            req.write('/')
