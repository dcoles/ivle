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

# App: server
# Author: Tom Conway, Matt Giuca
# Date: 13/12/2007

# Serves content to the user (acting as a web server for students files).
# For most file types we just serve the static file, but
# for python files, we evaluate the python script inside
# our safe execution environment.

import os

import cjson

from ivle import (studpath, interpret)
from ivle.database import User
from ivle.webapp.base.views import BaseView
from ivle.webapp.base.xhtml import XHTMLErrorView
from ivle.webapp.base.plugins import ViewPlugin, PublicViewPlugin
from ivle.webapp.errors import NotFound, Unauthorized, Forbidden

class ServeView(BaseView):
    def __init__(self, req, path):
        self.path = path

    def authorize(self, req):
        return req.user is not None

    def render(self, req):
        """Handler for the Server application which serves pages."""
        # Get the username of the student whose work we are browsing, and the
        # path on the local machine where the file is stored.
        (login, jail, path) = studpath.url_to_jailpaths(req.config, self.path)

        owner = User.get_by_login(req.store, login)
        if not owner:
            # There is no user.
            raise NotFound()

        self.serve(req, owner, jail, path)

    def serve(self, req, owner, jail, path):
        self.serve_file(req, owner, jail, path)

    def path_authorize(self, req):
        """Given a request, checks whether req.username is allowed to
        access req.path. Returns True on authz success, False on failure.

        This can't be done in the usual authorize(), because we rely on the
        jail being mounted.
        """
        # Private mode authorization: standard (only logged in user can access
        # their own files, and can access all of them).
        return studpath.authorize(req, req.user)

    def serve_file(self, req, owner, jail, path, download=False, files=None):
        """Serves a file, using one of three possibilities: interpreting it,
        serving it directly, or denying it and returning a 403 Forbidden error.
        No return value. Writes to req (possibly throwing an HTTP error).

        req: An IVLE request object.
        owner: The user who owns the file being served.
        jail: The user's jail.
        path: Filename in the jail.
        download:  Should the file be viewed in browser or downloaded
        """

        # We need a no-op trampoline run to ensure that the jail is mounted.
        # Otherwise we won't be able to authorise for public mode!
        noop_object = interpret.interpreter_objects["noop"]
        interpret.interpret_file(req, owner, jail, '', noop_object)

        # Authorize access. If failure, this throws a HTTP_FORBIDDEN error.
        if not self.path_authorize(req):
            raise Unauthorized()

        args = []
        if download:
            args.append('-d')

        if files and download:
            args += [os.path.join(path, f) for f in files]
        else:
            args.append(path)

        (out, err) = interpret.execute_raw(req.config, owner, jail, '/home',
                    os.path.join(req.config['paths']['share'],
                                 'services/serveservice'),
                    args)
        assert not err

        # Remove the JSON from the front of the response, and decode it.
        json = out.split('\n', 1)[0]
        out = out[len(json) + 1:]
        response = cjson.decode(json)

        if 'error' in response:
            if response['error'] == 'not-found':
                raise NotFound()
            elif response['error'] in ('is-directory', 'forbidden'):
                raise Forbidden()
            elif response['error'] == 'is-executable':
                # We need to execute it. Just run it with Python in the jail.
                interp_object = interpret.interpreter_objects["cgi-python"]
                interpret.interpret_file(req, owner, jail, response['path'],
                                         interp_object, gentle=True)
                return
            else:
                raise AssertionError('Unknown error from serveservice: %s' %
                                     response['error'])

        if download:
            req.headers_out["Content-Disposition"] = \
                         "attachment; filename=%s" % response['name']
        req.content_type = response['type']
        req.write(out)

class DownloadView(ServeView):
    def __init__(self, req, path):
        super(DownloadView, self).__init__(req, path)
        filelist = req.get_fieldstorage().getlist('path')
        if filelist:
            self.files = [f.value for f in filelist]
        else:
            self.files = None

    def serve(self, req, owner, jail, path):
        self.serve_file(req, owner, jail, path, download=True,files=self.files)

class PublicServeView(ServeView):
    def __init__(self, req, path):
        req.path = path # XXX: Needed because we don't have an app prefix.
        super(PublicServeView, self).__init__(req, path)

    def authorize(self, req):
        # Only accessible in public mode.
        return req.user is None

    def path_authorize(self, req):
        # Public mode authorization: any user can access any other user's
        # files, BUT the accessed file needs to have a file named '.published'
        # in its parent directory.
        return studpath.authorize_public(req)

    # We don't want to redirect to a login page on Unauthorized.
    @classmethod
    def get_error_view(cls, e):
        return XHTMLErrorView

class Plugin(ViewPlugin, PublicViewPlugin):
    urls = [
        ('serve/*path', ServeView),
        ('download/*path', DownloadView),
    ]

    public_urls = [
        ('~*path', PublicServeView),
    ]
