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
import plugins.console

from common import (util, studpath)

# url path for this app
THIS_APP = "files"

def handle(req):
    """Handler for the File Browser application."""

    # Work out where we are browsing
    browsepath = req.path
    if len(browsepath) == 0:
        # If no path specified, default to the user's home directory
        redirectPath = util.make_path(os.path.join(THIS_APP,req.user.login))
        req.throw_redirect(util.make_path(redirectPath))

    # Set request attributes
    req.content_type = "text/html"
    req.styles = [
        "media/browser/browser.css",
        "media/browser/listing.css",
        "media/browser/editor.css",
    ]
    req.scripts = [
        "media/common/json2.js",
        "media/common/codepress/codepress.js",
        "media/common/util.js",
        "media/browser/browser.js",
        "media/browser/listing.js",
        "media/browser/editor.js",
    ]
    # Let the console plugin insert its own styles and scripts
    plugins.console.insert_scripts_styles(req.scripts, req.styles)

    req.write_html_head_foot = True     # Have dispatch print head and foot
    # The page title should contain the name of the file being browsed
    req.title = browsepath.rsplit('/', 1)[-1]

    _, localpath = studpath.url_to_local(browsepath)
    if localpath is None:
        req.throw_error(req.HTTP_NOT_FOUND,
            "The path specified is invalid.")

    # Start writing data
    req.write("""
<!-- Top bar section -->

<div id="topbar">
  <div id="path">
    """)
    isdir = os.path.isdir(localpath)
    presentpath(req, browsepath, isdir)
    req.write("""
  </div>
  <div id="actions1">
""")
    present_actions1(req)
    req.write("""  </div>
  <div id="actions2">
""")
    present_actions2(req, isdir)
    req.write("""  </div>
</div>
<!-- End topbar -->

<!-- Body. The JavaScript places content here relevant to the path -->
<div id="filesbody">
</div>
<!-- End body -->
""")
    # Console
    plugins.console.present(req, windowpane=True)

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

def present_actions1(req):
    """
    Presents a set of links/buttons for the "actions1" row of the top bar.
    This is always exactly the same - the JavaScript will customize it later.
    """
    req.write("""    <a id="act_open" class="disabled">Open</a> :
    <a id="act_serve"
        title="View this file on the web, running your code if this is a CGI file"
        class="disabled" target="_blank">Serve</a> :
    <a id="act_run" title="Run the selected Python file in the console"
        class="disabled">Run</a> :
    <a id="act_download" class="choice">Download</a> :
    <a title="Refresh the current page" onclick="refresh()"
        class="choice">Refresh</a><span id="moreactions_area"> :
    <select id="moreactions" onchange="handle_moreactions()"
        onblur="handle_moreactions()">
      <option class="moreactions" value="top"
        selected="selected">More actions...</option>

      <option class="heading" disabled="disabled">Publishing</option>
      <option id="act_publish" class="disabled" disabled="disabled"
        title="Make it so this directory can be seen by anyone on the web"
        value="publish">Publish</option>
      <option id="act_share" class="disabled" disabled="disabled"
        title="Get a link to this published file, to give to friends"
        value="share">Share this file</option>
      <option id="act_submit" class="disabled" disabled="disabled"
        title="Submit the selected files for an assignment"
        value="submit">Submit</option>

      <option class="heading" disabled="disabled">File actions</option>
      <option id="act_rename" class="disabled" disabled="disabled"
        title="Change the name of this file" value="rename">Rename</option>
      <option id="act_delete" class="disabled" disabled="disabled"
        title="Delete the selected files" value="delete">Delete</option>
      <option id="act_copy" class="disabled" disabled="disabled"
        title="Prepare to copy the selected files to another directory"
        value="copy">Copy</option>
      <option id="act_cut" class="disabled" disabled="disabled"
        title="Prepare to move the selected files to another directory"
        value="cut">Cut</option>

      <option class="heading" disabled="disabled">Directory actions</option>
      <option id="act_paste" class="choice"
        title="Paste the copied or cut files to the current directory"
        value="paste">Paste</option>
      <option id="act_newfile" class="choice"
        title="Open a new file for editing in the current directory"
        value="newfile">New File</option>
      <option id="act_mkdir" class="choice"
        title="Make a new subdirectory in the current directory"
        value="mkdir">New Directory</option>
      <option id="act_upload" class="choice"
        title="Upload a file to the current directory"
        value="upload">Upload File</option>

      <option class="heading" disabled="disabled">Subversion</option>
      <option id="act_svnadd" class="disabled" disabled="disabled"
        title="Schedule the selected temporary files to be added permanently"
        value="svnadd">Add</option>
      <option id="act_svndiff" class="disabled" disabled="disabled"
        title="View any changes to the selected file since its last committed state"
        value="svndiff">Diff</option>
      <option id="act_svnrevert" class="disabled" disabled="disabled"
        title="Restore the selected files back to their last committed state"
        value="svnrevert">Revert</option>
      <option id="act_svncommit" class="disabled" disabled="disabled"
        title="Commit any changes to the permanent repository"
        value="svncommit">Commit</option>
      <option id="act_svncheckout" class="disabled" disabled="disabled"
        title="Re-check out your default directories"
        value="svncheckout">Re-Checkout</option>
    </select></span>
""")

def present_actions2(req, isdir):
    """
    Presents a set of links/buttons for the "actions2" row of the top bar.
    This depends on whether it is a directory (listing) or normal file
    (editor).
    """
    if isdir:
        req.write("""    <form target="upload_iframe"
          action="%s"
          enctype="multipart/form-data" method="post">
      Select:
      <a onclick="action_selectall(true)"
          title="Select all files in this directory">All</a> :
      <a onclick="action_selectall(false)"
          title="Deselect all files in this directory">None</a>

      <span style="display:none" id="uploadpanel">| Upload file:
        <input type="hidden" value="putfiles" name="action" />
        <input type="hidden" value="" name="path" />
        <input type="file" name="data" />
        <input type="checkbox" checked="on" value="true" name="unpack"
          />Unpack zip file
        <input type="button" onclick="show_uploadpanel(false)" value="Hide" />
        <input type="submit" value="Send" />
      </span>
      <!-- This iframe is for making a call to upload the file without
           refreshing the page. (It will refresh the listing). -->
      <iframe onload="upload_callback()" style="display: none;"
          name="upload_iframe" id="upload_iframe"></iframe>
    </form>
""" % cgi.escape(util.make_path(os.path.join("fileservice", req.path))))
    else:
        req.write("""    <p>Save as: 
      <input type="text" size="30" id="save_filename" value="%s" />
      <input type="button" id="save_button" value="Save" onclick="save_file()" />
    </p>
""" % cgi.escape(req.path))
