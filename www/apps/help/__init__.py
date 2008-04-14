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
import copy
import conf
from conf import apps

# TODO: Nicer 404 errors

def handle(req):
    """Handler for the Help application."""
    (appurl, subpath) = util.split_path(req.path)

    if appurl is None:
        show_help_menu(req)
    else:
        # app must be valid and have help available
        if appurl not in conf.apps.app_url:
            req.throw_error(req.HTTP_NOT_FOUND)
        app = conf.apps.app_url[appurl]
        if not app.hashelp:
            req.throw_error(req.HTTP_NOT_FOUND)
        # subpath must be empty, for now, as there is only one help file per app
        if subpath != "":
            req.throw_error(req.HTTP_NOT_FOUND)
        show_help_app(req, app)

def show_help_menu(req):
    """Show the help menu."""

    # Set request attributes
    req.content_type = "text/html"
    req.write_html_head_foot = True

    # Start writing data
    req.write('<div id="ivle_padding">\n')
    req.write("<h1>Help</h1>\n")

    # Write a list of links to all apps with help modules
    req.write("<ul>\n")
    # Tab apps, in order of tabs
    for appurl in conf.apps.apps_in_tabs:
        app = conf.apps.app_url[appurl]
        if app.hashelp:
            req.write('  <li><a href="%s">%s</a></li>\n'
                % (os.path.join(util.make_path("help"), appurl), app.name))
    # Terms of Service
    req.write('  <li><a href="%s">Terms of Service</a></li>\n'
        % (util.make_path("tos")))
    req.write("</ul>\n")
    req.write('</div>\n')

def show_help_app(req, app):
    """Show help for an application."""
    helpfile = os.path.join(util.make_local_path("apps"), app.dir, "help.html")

    # Set request attributes
    req.content_type = "text/html"
    req.write_html_head_foot = True
    req.styles = ["media/help/help.css"]

    # Start writing data
    req.write('<div id="ivle_padding">\n')
    req.write("<h1>Help - %s</h1>\n" % app.name)

    # Print out the contents of the HTML help file
    req.sendfile(helpfile)
    req.write('</div>\n')
