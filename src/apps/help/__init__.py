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

# App: help
# Author: Matt Giuca
# Date: 12/12/2007

# This is an IVLE application.
# A sample / testing application for IVLE.

from common import util
import os
import conf
from conf import apps

# TODO: Nicer 404 errors

def handle(req):
    """Handler for the Help application."""
    (appurl, subpath) = util.split_path(req.path)
    # app must be valid and have help available
    if appurl not in conf.apps.app_url:
        req.throw_error(req.HTTP_NOT_FOUND)
    app = conf.apps.app_url[appurl]
    if not app.hashelp:
        req.throw_error(req.HTTP_NOT_FOUND)
    # subpath must be empty, for now, as there is only one help file per app
    if subpath != "":
        req.throw_error(req.HTTP_NOT_FOUND)
    helpfile = os.path.join(util.make_local_path("apps"), app.dir, "help.html")

    # Set request attributes
    req.content_type = "text/html"
    req.write_html_head_foot = True

    # Start writing data
    req.write("<h1>Help - %s</h1>\n" % app.name)

    # Print out the contents of the HTML help file
    req.sendfile(helpfile)
