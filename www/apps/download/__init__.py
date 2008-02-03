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

from common import (util, studpath, zip)
import conf

import functools
import os
import mimetypes
import StringIO

# Serve all files as application/octet-stream so the browser presents them as
# a download.
default_mimetype = "application/octet-stream"
zip_mimetype = "application/zip"

def handle(req):
    """Handler for the Download application which serves files for
    download."""
    # Make sure the logged in user has permission to see this file
    studpath.authorize(req)

    zipmode = False
    zipbasepath = None
    zipfilename = None
    path = None

    req.write_html_head_foot = False

    # If any "path=" variables have been supplied, bring these into a list and
    # make a zip file instead.
    fields = req.get_fieldstorage()
    paths = fields.getlist("path")
    if len(paths) > 0:
        zipmode = True
        zipbasepath = req.path
        zipfilename = os.path.basename(zipbasepath)
        for i in range(0, len(paths)):
            paths[i] = paths[i].value
    else:
        # Otherwise, just serve directly (unless it's a directory)
        (_, path) = studpath.url_to_local(req.path)
        if path is None:
            # TODO: Nicer 404 message?
            req.throw_error(req.HTTP_NOT_FOUND)
        elif not os.access(path, os.R_OK):
            req.throw_error(req.HTTP_NOT_FOUND)
        # If it's a directory, serve as a zip file
        if os.path.isdir(path):
            zipmode = True
            # Zip it from the perspective of its own parent.
            # That way it will be a directory in the top level of the zip
            # file.
            path = req.path
            if path[-1] == os.sep: path = path[:-1]
            splitpath = path.rsplit(os.sep, 1)
            if len(splitpath) == 1:
                zipbasepath = ''
                paths = [path]
            else:
                zipbasepath = splitpath[0]
                paths = [splitpath[1]]
            zipfilename = paths[0]

    if zipmode:
        req.content_type = zip_mimetype
        # zipfilename is some filename. Strip trailing slash or extension,
        # and add ".zip".
        if zipfilename == '':
            zipfilename = "files"
        elif zipfilename[-1] == '/':
            zipfilename = zipfilename[:-1]
        elif '.' in zipfilename:
            zipfilename = zipfilename[:zipfilename.rindex('.')]
        zipfilename += ".zip"
        req.headers_out["Content-Disposition"] = ("attachment; filename=" +
            zipfilename)
        zipfile = StringIO.StringIO()
        zip.make_zip(zipbasepath, paths, zipfile)
        req.write(zipfile.getvalue())
    else:
        req.content_type = default_mimetype
        req.sendfile(path)
