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

from common import util

def handle(req):
    """Handler for the File Browser application."""

    # Set request attributes
    req.content_type = "text/html"
    req.styles = ["media/browser/browser.css"]
    req.scripts = [
        "media/common/json2.js",
        "media/common/util.js",
        "media/browser/browser.js",
    ]
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Start writing data
    req.write("""
<!-- Top bar section -->

<div id="topbar">
<h2>IVLE File Browser</h2>
<p id="path"></p>
<p><input type="button" value="Refresh" onclick="action_refresh()" />
<input type="button" value="New File" onclick="action_newfile()" />
<input type="button" value="Commit All" onclick="action_svncommitall()" /></p>
</div>
<!-- End topbar -->

<!-- Centre section - files and side panel -->
<!-- Using a table-based layout, for reasons of sanity -->
<table id="middle"><tr>

<!-- File table -->
<td id="filetable">

<div id="filetablediv">

<table width="100%%">
<thead>
<tr class="rowhead">
    <th class="col-check"></th>
    <th colspan="3" class="col-filename"><a href="javascript:alert(&quot;Sort by name&quot;)" title="Sort by name">Filename</a>
        <img src="%s/images/interface/sortdown.png" alt="*" /></th>
    <th class="col-size"><a href="javascript:alert(&quot;Sort by file size&quot;)" title="Sort by file size">Size</a></th>
    <th class="col-date"><a href="javascript:alert(&quot;Sort by date modified&quot;)" title="Sort by date modified">Modified</a></th>
</tr>
</thead>
<tbody id="files">
</tbody>
</table>
</div>
</td>
<!-- End filetable -->

<!-- Side panel -->

<td id="sidepanel">
</td>
<!-- End sidepanel -->

</tr></table>
<!-- End middle -->

<!-- Bottom status bar -->

<div id="statusbar">
<table>
<tr><td>5 files, 14 kB</td></tr>
</table>
</div>
<!-- End statusbar -->

</body>
</html>
""" %
    # All the %ses above refer to the location of the IVLE media directory
    util.make_path("media")
)

