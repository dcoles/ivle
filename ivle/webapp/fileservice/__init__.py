# IVLE
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

# Author: Matt Giuca, Will Grant

'''Service for accessing a jail's filesystem.

This application is a wrapper around the library module fileservice, running
it through trampoline.

It receives file handling instructions as requests, performs actions on the
student's workspace, and returns directory listings in JSON.

See the documentation in ivle.fileservice_lib for details.
'''

import os.path

import ivle.interpret
from ivle.webapp.base.views import BaseView
from ivle.webapp.base.plugins import ViewPlugin
from ivle.webapp.urls import INF
from ivle.webapp import ApplicationRoot

class FileserviceFile(object):
    def __init__(self, root, path):
        self.root = root
        self.path = path

# XXX: Writes to req directly. This is a direct port of the legacy version.
#      This needs to be rewritten soon.
class FileserviceView(BaseView):
    def authorize(self, req):
        return req.user is not None

    def render(self, req):
        """Handler for the File Services application."""
        if len(self.context.path) == 0:
            # If no path specified, default to the user's home directory
            req.throw_redirect(req.make_path(os.path.join('fileservice',
                                                          req.user.login)))

        interp_object = ivle.interpret.interpreter_objects["cgi-python"]
        user_jail_dir = os.path.join(req.config['paths']['jails']['mounts'],
                                     req.user.login)

        ivle.interpret.interpret_file(req, req.user, user_jail_dir,
                                  os.path.join(req.config['paths']['share'],
                                               'services/fileservice'),
                                  interp_object, gentle=False)

def root_to_fileservicefile(root, *path):
    return FileserviceFile(root, os.path.join(*path) if path else '')

class Plugin(ViewPlugin):
    forward_routes = [(ApplicationRoot, 'fileservice',
                       root_to_fileservicefile, INF),
                      ]
    views = [(FileserviceFile, '+index', FileserviceView)]
