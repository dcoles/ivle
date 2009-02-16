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

# App: download
# Author: Matt Giuca
# Date: 17/1/2008

# Serves content to the user (acting as a web server for students files).
# Unlike "serve", all content is served as a static file, and with the
# application/octet-stream mime type.
# Also can serve directories or multiple files, automatically zipping them up.
# Uses a large chunk of code from "serve"

import StringIO

from ivle import studpath
from apps import server

# Serve all files as application/octet-stream so the browser presents them as
# a download.
default_mimetype = "application/octet-stream"
zip_mimetype = "application/zip"

def handle(req):
    """Handler for the Download application which serves files for
    download."""

    req.write_html_head_foot = False

    # Get the username of the student whose work we are browsing, and the path
    # on the local machine where the file is stored.
    (user, path) = studpath.url_to_local(req.path)

    if user is None:
        req.throw_error(req.HTTP_NOT_FOUND,
            "The path specified is invalid.")

    # Use the code from server to avoid duplication
    server.serve_file(req, req.user, path, download=True)
