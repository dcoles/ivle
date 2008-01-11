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
<h1>IVLE File Browser</h1>
<p id="path"><a href="javascript:alert(&quot;Navigate to home&quot;)">home</a> /
    <a href="javascript:alert(&quot;Navigate to home/work&quot;)">work</a></p>
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
    <th colspan="2" class="col-filename"><a href="javascript:alert(&quot;Sort by name&quot;)" title="Sort by name">Filename</a>
        <img src="%s/images/interface/sortdown.png" alt="*" /></th>
    <th class="col-size"><a href="javascript:alert(&quot;Sort by file size&quot;)" title="Sort by file size">Size</a></th>
    <th class="col-date"><a href="javascript:alert(&quot;Sort by date modified&quot;)" title="Sort by date modified">Modified</a></th>
</tr>
</thead>
<tbody id="files">
<tr class="row1">
    <td class="col-check"><input type="checkbox" title="Select this file" /></td>
    <td class="col-icons"><img src="%s/images/mime/dir.png" width="22" height="22" title="Directory" alt="" />
        <img src="%s/images/svn/normal.png" width="22" height="22" title="Permanent file" alt="" /></td>
    <td class="col-filename"><a href="javascript:alert(&quot;Navigate to home/work/subdir1&quot;)" title="subdir1">subdir1</a></td>
    <td class="col-size"></td>
    <td class="col-date"><span title="Dec 3 2007, 3:47 PM">Dec 3</span></td>
</tr>
<tr class="row2">
    <td class="col-check"><input type="checkbox" title="Select this file" /></td>
    <td class="col-icons"><img src="%s/images/mime/dir.png" width="22" height="22" title="Directory" alt="" />
        <img src="%s/images/svn/unversioned.png" width="22" height="22" title="Temporary file" alt="" /></td>
    <td class="col-filename"><a href="javascript:alert(&quot;Navigate to home/work/subdir2&quot;)" title="subdir2">subdir2</a></td>
    <td class="col-size"></td>
    <td class="col-date"><span title="Dec 8 2007, 11:37 AM">Today, 11:37 AM</span></td>
</tr>
<tr class="row1sel">
    <td class="col-check"><input type="checkbox" title="Select this file" checked="true" /></td>
    <td class="col-icons"><img src="%s/images/mime/py.png" width="22" height="22" title="Python source code" alt="" />
        <img src="%s/images/svn/modified.png" width="22" height="22" title="Permanent file (modified)" alt="" /></td>
    <td class="col-filename">hello.py</td>
    <td class="col-size">60 B</td>
    <td class="col-date"><span title="Dec 8 2007, 2:50 PM">Today, 2:50 PM</span></td>
</tr>
<tr class="row2">
    <td class="col-check"><input type="checkbox" title="Select this file" /></td>
    <td class="col-icons"><img src="%s/images/mime/txt.png" width="22" height="22" title="Text file" alt="" />
        <img src="%s/images/svn/unversioned.png" width="22" height="22" title="Temporary file" alt="" /></td>
    <td class="col-filename">world</td>
    <td class="col-size">24 B</td>
    <td class="col-date"><span title="Dec 5 2007, 1:40 AM">3 days ago</span></td>
</tr>
<tr class="row1">
    <td class="col-check"><input type="checkbox" title="Select this file" /></td>
    <td class="col-icons"><img src="%s/images/mime/txt.png" width="22" height="22" title="Text file" alt="" />
        <img src="%s/images/svn/unversioned.png" width="22" height="22" title="Temporary file" alt="" /></td>
    <td class="col-filename">File names that are extremely long are not condensed, merely they extend very far and wrap if necessary.txt</td>
    <td class="col-size">14 kB</td>
    <td class="col-date"><span title="Nov 11 2007, 9:14 AM">Nov 11</span></td>
</tr>
</tbody>
</table>
</div>
</td>
<!-- End filetable -->

<!-- Side panel -->

<td id="sidepanel">
<!-- This section is entirely dynamically generated by selecting files.
     An example follows -->
     <p><img src="%s/images/mime/large/py.png" title="Python source code" alt="" /></p>
     <h1>hello.py</h1>
     <p>Python source code</p>
     <p><img src="%s/images/svn/modified.png" width="22" height="22" title="Permanent file (modified)" alt="" /><br />Permanent file (modified)</p>
     <p>Size: 60 bytes</p>
     <p>Modified: Dec 8 2007, 2:50 PM</p>
     <h2>Actions</h2>
     <p><a href="">Edit</a></p>
     <p><a href="">Run in Browser</a></p>
     <p><a href="">Run in Console</a></p>
     <p><a href="">Rename</a></p>
     <p><a href="">Download</a></p>
     <p><a href="">Cut</a></p>
     <p><a href="">Copy</a></p>
     <h2>Subversion</h2>
     <p><a href="">Commit</a></p>
     <p><a href="">Update</a></p>
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
    (util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"),
    util.make_path("media"))
)

