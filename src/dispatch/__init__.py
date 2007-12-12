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

# Module: dispatch
# Author: Matt Giuca
# Date: 11/12/2007

# This is a mod_python handler program. The correct way to call it is to have
# Apache send all requests to be handled by the module 'dispatch'.

# Top-level handler. Handles all requests to all pages in IVLE.
# Handles authentication (not authorization).
# Then passes the request along to the appropriate ivle app.

from mod_python import apache
import os
import os.path
import conf
import conf.apps

import request

root_dir = conf.root_dir

def handler(req):
    """Handles a request which may be to anywhere in the site except media.
    Intended to be called by mod_python, as a handler.

    req: An Apache request object.
    """
    # Make the request object into an IVLE request which can be passed to apps
    req = request.Request(req)

    # TEMP: Dummy (test) handler
    req.content_type = "text/html"
    req.write("<html>\n")
    req.write("<p>Hello, IVLE!</p>\n")
    req.write('<p><img src="' + make_path("media/images/mime/dir.png")
        + '" /> ')
    req.write(str(req.uri))
    req.write("</p>\n")

    print_apps_list(req)

    req.write("</html>")
    return apache.OK

def make_path(path):
    """Given a path relative to the IVLE root, makes the path relative to the
    site root using conf.root_dir. This path can be used in URLs sent to the
    client."""
    return os.path.join(root_dir, path)

def print_apps_list(file):
    """Prints all app tabs, as a UL. Prints a list item for each app that has
    a tab.

    file: Object with a "write" method - ie. the request object.
    Reads from: conf
    """
    file.write('<ul class="apptabs">\n')

    for urlname in conf.apps.apps_in_tabs:
        app = conf.apps.app_url[urlname]
        file.write('  <li><a href="')
        file.write(make_path(app.dir))
        file.write('">')
        file.write(app.name)
        file.write('</a></li>\n')

    file.write('</ul>\n')
