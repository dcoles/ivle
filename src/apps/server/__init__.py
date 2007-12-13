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
# Author: Tom Conway
# Date: 13/12/2007

# Serves content to the user (acting as a web server for students files).
# For most file types we just serve the static file, but
# for python files, we evaluate the python script inside
# our safe execution environment.

from common import util
import conf

import functools
import mimetypes
import os

executable_types = {
    'text/x-python' : functools.partial(server.cgi.handler, '/usr/bin/python')
}

def handle(req):
    """Handler for the Server application which serves pages."""

    mimetypes.init()
    (type, encoding) = mimetypes.guess_type(req.path)

    if type is None:
        type = 'text/plain'

    if type in executable_types:
        return executable_types[type](req)

    # We're expecting paths are all of the form <usr>/...
    parts = req.path.split(os.sep)
    if len(parts) == 0:
        # FIXME
        raise Exception, "empty path!"

    usr = parts[0]

    req.content_type = type
    if encoding != None:
        req.content_encoding = encoding

    req.write_html_head_foot = False

    path = os.path.join(conf.student_dir, usr, 'home', req.path)

    req.sendfile(path)
