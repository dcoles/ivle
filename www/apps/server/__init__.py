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

from common import (util, studpath, interpret)
import conf
import conf.app.server

import os
import mimetypes

def handle(req):
    """Handler for the Server application which serves pages."""
    req.write_html_head_foot = False

    # Get the username of the student whose work we are browsing, and the path
    # on the local machine where the file is stored.
    (user, path) = studpath.url_to_local(req.path)

    if user is None:
        req.throw_error(req.HTTP_NOT_FOUND,
            "The path specified is invalid.")

    serve_file(req, user, path)

def authorize(req):
    """Given a request, checks whether req.username is allowed to
    access req.path. Returns None on authorization success. Raises
    HTTP_FORBIDDEN on failure.
    """
    if req.publicmode:
        # Public mode authorization: any user can access any other user's
        # files, BUT the accessed file needs to have its "ivle:published" flag
        # turned on in the SVN status.
        studpath.authorize_public(req)
    else:
        # Private mode authorization: standard (only logged in user can access
        # their own files, and can access all of them).
        studpath.authorize(req)

def serve_file(req, owner, filename):
    """Serves a file, using one of three possibilities: interpreting the file,
    serving it directly, or denying it and returning a 403 Forbidden error.
    No return value. Writes to req (possibly throwing a server error exception
    using req.throw_error).
    
    req: An IVLE request object.
    owner: Username of the user who owns the file being served.
    filename: Filename in the local file system.
    """
    # Authorize access. If failure, this throws a HTTP_FORBIDDEN error.
    authorize(req)

    # First get the mime type of this file
    # (Note that importing common.util has already initialised mime types)
    (type, _) = mimetypes.guess_type(filename)
    if type is None:
        type = conf.mimetypes.default_mimetype

    # If this type is to be interpreted
    if os.path.isdir(filename):
        # 403 Forbidden error for visiting a directory
        # (Not giving a directory listing, since this can be seen by
        # the world at large. Directory contents are private).
        req.throw_error(req.HTTP_FORBIDDEN,
            "The path specified is a directory.")
    elif type in conf.app.server.interpreters:
        interp_name = conf.app.server.interpreters[type]
        try:
            # Get the interpreter function object
            interp_object = interpret.interpreter_objects[interp_name]
            (_, jail_dir, path) = studpath.url_to_jailpaths(req.path)
        except KeyError:
            req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR,
                "The interpreter for this file has not been "
                "configured correctly.")
        interpret.interpret_file(req, owner, jail_dir, path, interp_object)

    else:
        # Otherwise, use the blacklist/whitelist to see if this file should be
        # served or disallowed
        if conf.app.server.blacklist_served_filetypes:
            toserve = type not in conf.app.server.served_filetypes_blacklist
        else:
            toserve = type in conf.app.server.served_filetypes_whitelist

        # toserve or not toserve
        if not toserve:
            req.throw_error(req.HTTP_FORBIDDEN,
                "Files of this type are not allowed to be served.")
        else:
            serve_file_direct(req, filename, type)

def serve_file_direct(req, filename, type):
    """Serves a file by directly writing it out to the response.

    req: An IVLE request object.
    filename: Filename in the local file system.
    type: String. Mime type to serve the file with.
    """
    if not os.access(filename, os.R_OK):
        req.throw_error(req.HTTP_NOT_FOUND,
            "The specified file does not exist.")
    req.content_type = type
    req.sendfile(filename)
