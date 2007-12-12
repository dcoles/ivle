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

from request import Request
import html
import common.util
from common.util import make_path

def handler(req):
    """Handles a request which may be to anywhere in the site except media.
    Intended to be called by mod_python, as a handler.

    req: An Apache request object.
    """
    # Make the request object into an IVLE request which can be passed to apps
    req = Request(req, html.write_html_head)

    # TODO: Check req.app to see if it is valid. 404 if not.

    # TODO: Check if app requires auth. If so, perform authentication and
    # login.

    # TODO: If user did not specify an app, HTTP redirect to default app and
    # exit.

    # Call the specified app with the request object
    # TODO: Call a real app.
    test_app(req)

    # When done, write out the HTML footer if the app has requested it
    if req.write_html_head_foot:
        # MAKE SURE we write the head (we would never do that if the app, nor
        # write_html_foot, ever writes anything - so just to be sure).
        req.write("", flush=0)
        html.write_html_foot(req)

    # Have Apache output its own HTML code if non-200 status codes were found
    return req.status

def test_app(req):
    """This (temporary) function serves as an IVLE application. It takes an
    IVLE request and conforms to the application API."""
    # TEMP: Dummy (test) handler

    # Set request attributes
    req.content_type = "text/html"
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Start writing data
    req.write("<p>Hello, IVLE!</p>\n")
    req.write('<p><img src="' + make_path("media/images/mime/dir.png")
        + '" /> ')
    req.write(str(req.uri))
    req.write("</p>\n")

    print_apps_list(req)

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
