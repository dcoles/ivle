# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
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

# Author: Matt Giuca, Nick Chadwick

"""
The file browser application. Presents an Ajax-based interface to the
student's subversion workspace.

Note that there is virtually no server-side code for this application. It
simply presents static HTML and JavaScript, and all server-side activities
take place in the FileService app (for handling Ajax requests).
"""

from ivle.webapp.base.plugins import ViewPlugin, CookiePlugin, MediaPlugin
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.errors import NotFound
from ivle.webapp.filesystem import make_path_segments
from ivle.webapp import ApplicationRoot

import os.path
import cgi

import ivle.svn

class BrowserView(XHTMLView):
    """
    The view for the browser
    """
    template = 'template.html'
    tab = 'files'
    help = 'Filesystem/Browser'

    subpath_allowed = True

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        if len(self.path) == 0:
            # If no path specified, default to the user's home directory
            redirectPath = req.make_path(os.path.join('files', req.user.login))
            req.throw_redirect(redirectPath)

        # Set request attributes
        self.plugin_styles[Plugin] = ['browser.css',
                                      'listing.css',
                                      'editor.css']
        self.plugin_scripts[Plugin] = ['browser.js',
                                       'listing.js',
                                       'editor.js',
                                       'specialhome.js',
                                       'codepress/codepress.js']
        self.scripts_init = ["browser_init"]

        # Start writing data

        # TODO: Set this properly. We can't get into the jail from server-side
        # code at the moment, so we can't determine this.
        isdir = False

        revision = ivle.svn.revision_from_string(
                         req.get_fieldstorage().getfirst('r'))
        try:
            revno = revision.number
        except:
            revno = None

        ctx['isdir'] = isdir
        ctx['revno'] = revno

        ctx['paths'] = make_path_segments(req.path, revno)

        self.gen_actions(req, ctx)

        # The page title should contain the name of the file being browsed
        ctx['title'] = os.path.normpath(self.path).rsplit('/', 1)[-1]

        ctx['fileservice_action'] = req.make_path(os.path.join("fileservice",
                                                               self.path))
        ctx['filename'] = cgi.escape(self.path)

    @property
    def path(self):
        return os.path.join(*self.subpath) if self.subpath else ''

    #TODO: Move all this logic into the template
    def gen_actions(self, req, ctx):
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
            ('submit',  ['Submit', 'Submit the selected files for a project'])
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

class BrowserRedirectView(XHTMLView):
    def authorize(self, req):
        return req.user is not None

    def render(self, req):
        redirect_path = req.make_path(os.path.join('files', req.user.login))
        req.throw_redirect(redirect_path)

class Plugin(ViewPlugin, CookiePlugin, MediaPlugin):
    views = [(ApplicationRoot, 'files', BrowserView),
             (ApplicationRoot, '+index', BrowserRedirectView),
             ]

    tabs = [
        ('files', 'Files', 'Access and edit your files',
         'browser.png', 'files', 1)
    ]

    cookies = {'clipboard': None}

    help = {'Filesystem': {'Browser': 'help.html'}}

    media = 'media'
