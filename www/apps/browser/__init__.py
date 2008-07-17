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

from common import (util, studpath)
import common.svn

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
    req.scripts_init = [
        "browser_init",
    ]

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
    # FIXME: This isn't completely reliable! We're not inside the jail, so we
    # can't know the type for sure. This is now only used for adding a / to the
    # end of displayed paths, so I'm leaving this although it will often break.
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
    present_actions2(req)
    req.write("""  </div>
</div>
<!-- End topbar -->

<!-- Body. The JavaScript places content here relevant to the path -->
<div id="filesbody">
</div>
<!-- End body -->
""")

def presentpath(req, path, isdir):
    """
    Presents a path list (address bar inside the page) for clicking.
    Writes to req, expecting to have just written the opening div containing
    the listing.
    This will also have a revision indicator on the end, if we are viewing a
    revision.
    """
    href_path = util.make_path(THIS_APP)
    nav_path = ""

    revision = common.svn.revision_from_string(
                     req.get_fieldstorage().getfirst('r'))

    try: 
        revno = revision.number
    except:
        revno = None
       
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

    if revno is not None:
        req.write(' (revision %d)' % revno)

def present_actions1(req):
    """
    Presents a set of links/buttons for the "actions1" row of the top bar.
    This is always exactly the same - the JavaScript will customize it later.
    """
    # Set up our actions. The second field of each group is whether to disable
    # the items by default.
    moreactions = [
      ('Publishing', True, [
        ('publish', ['Publish',          'Make it so this directory can be seen by anyone on the web']),
        ('share',   ['Share this file',  'Get a link to this published file, to give to friends']),
        ('submit',  ['Submit', 'Submit the selected files for an assignment'])
      ]),
      ('File actions', True, [
        ('rename',  ['Rename',           'Change the name of this file']),
        ('delete',  ['Delete',           'Delete the selected files']),
        ('copy',    ['Copy',             'Prepare to copy the selected files to another directory']),
        ('cut',     ['Cut',              'Prepare to move the selected files to another directory'])
      ]),
      ('Directory actions', False, [
        ('paste',   ['Paste',            'Paste the copied or cut files into the current directory']),
        ('newfile', ['New File',         'Open a new file for editing in the current directory']),
        ('mkdir',   ['New Directory',    'Make a new subdirectory in the current directory']),
        ('upload',  ['Upload File',      'Upload a file to the current directory'])
      ]),
      ('Subversion', True, [
        ('svnadd',      ['Add',          'Schedule the selected temporary files to be added permanently']),
        ('svndiff',     ['Diff',         'View any changes to the selected file since its last committed state']),
        ('svnrevert',   ['Revert',       'Restore the selected files back to their last committed state']),
        ('svncommit',   ['Commit',       'Commit any changes to the permanent repository']),
        ('svnlog',      ['View Log',     'View the log of commits of the selected file']),
        ('svncheckout', ['Re-checkout',  'Re-checkout your default directories'])
      ])
    ]

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
""")

    for (name, disablement, group) in moreactions:
        if disablement:
            disable = 'class="disabled" disabled="disabled"'
        else:
            disable = ''
        req.write('<optgroup label="%s">' % name)
        for (id, bits) in group:
            req.write('<option id="act_%s" %s title="%s" value="%s">%s</option>'
                      % (id, disable, bits[1], id, bits[0]))
        req.write('</optgroup>')

    req.write('</select></span>')

def present_actions2(req):
    """
    Presents a set of links/buttons for the "actions2" row of the top bar.
    This depends on whether it is a directory (listing) or normal file
    (editor), but we'll let the JavaScript decide which.
    """
    req.write("""    <form id="actions2_directory"
          target="upload_iframe"
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

    req.write("""    <p id="actions2_file">
      <input type="button" id="save_button" value="Save" onclick="save_file('%s')" />
      <input type="button" id="saveas_button" value="Save As..." onclick="save_file_as('%s')" />
      <select id="highlighting_select" onchange="highlighting_changed(this)">
          <option value="text">Text</option>
          <option value="python">Python</option>
          <option value="html">HTML</option>
          <option value="javascript">JavaScript</option>
          <option value="css">CSS</option>
      </select>
    </p>
""" % ((cgi.escape(req.path),) * 2))
