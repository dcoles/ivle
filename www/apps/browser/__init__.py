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

from ivle import (util, studpath)
import ivle.svn

import genshi
import genshi.core
import genshi.template

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

    ctx = genshi.template.Context()

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
        "media/browser/specialhome.js",
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

    # FIXME: This isn't completely reliable! We're not inside the jail, so we
    # can't know the type for sure. This is now only used for adding a / to the
    # end of displayed paths, so I'm leaving this although it will often break.
    isdir = os.path.isdir(localpath)
    ctx['isdir'] = isdir
    gen_path(req, browsepath, ctx)
    gen_actions(req, ctx)
    
    ctx['fileservice_action'] = util.make_path(os.path.join("fileservice", req.path))
    ctx['filename'] = cgi.escape(req.path)

    loader = genshi.template.TemplateLoader(".", auto_reload=True)
    tmpl = loader.load(util.make_local_path("apps/browser/template.html"))
    
    req.write(tmpl.generate(ctx).render('html')) #'xhtml', doctype='xhtml'))

#TODO: Move all this logic into the template
def gen_path(req, path, ctx):

    href_path = util.make_path(THIS_APP)
    nav_path = ""
    revision = ivle.svn.revision_from_string(
                     req.get_fieldstorage().getfirst('r'))
    try: 
        revno = revision.number
    except:
        revno = None
      
    ctx['revno'] = revno
    
    # Create all of the paths
    pathlist = path.split("/")
    ctx['paths'] = []
    for path_seg in pathlist:
        if path_seg == "":
            continue
        new_seg = {}
        
        nav_path = nav_path + path_seg
        href_path = href_path + '/' + path_seg
        
        new_seg['path'] = path_seg        
        new_seg['nav_path'] = nav_path
        new_seg['href_path'] = href_path
        if revno is not None:
            new_seg['href_path'] += '?r=%d' % revno
        
        ctx['paths'].append(new_seg)


def gen_actions(req, ctx):
    """
    Presents a set of links/buttons for the "actions1" row of the top bar.
    This is always exactly the same - the JavaScript will customize it later.
    """
    # Set up our actions. The second field of each group is whether to disable
    # the items by default.
    ctx['moreactions'] = [
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
        ('svncut',      ['Svn Cut',      'Prepare to move the selected files to another directory, maintaining history']),
        ('svncopy',     ['Svn Copy',     'Prepare to copy the selected files to another directory, maintaining history']),
        ('svnadd',      ['Add',            'Schedule the selected temporary files to be added permanently']),
        ('svnremove',   ['Remove',         'Schedule the selected permanent files to be removed']),
        ('svndiff',     ['Diff',           'View any changes to the selected file since its last committed state']),
        ('svnrevert',   ['Revert',         'Restore the selected files back to their last committed state']),
        ('svnupdate',   ['Update',         'Update your files with changes from the permanent repository']),
        ('svncommit',   ['Commit',         'Commit any changes to the permanent repository']),
        ('svnresolved', ['Mark Resolved',  'Mark a conflicted file as being resolved']),
        ('svnlog',      ['View Log',       'View the log of commits of the selected file']),
      ])
    ]
