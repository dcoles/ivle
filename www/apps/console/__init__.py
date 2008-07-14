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

# App: console
# Author: Matt Giuca
# Date: 30/1/2008

# Console application.
# Presents a Python console as a complete app. (This simply imports the
# Console plugin - see plugins/console).

from common import util
import plugins.console

def handle(req):
    """Handler for the Console application."""

    # Set request attributes
    req.content_type = "text/html"
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Let the plugin mandate the scripts and styles to use
    req.scripts = [
        "media/console/console.js",
        "media/console/console_app.js" ]
    req.styles = [
        "media/console/console.css",
        "media/console/console_app.css" ]
    req.scripts_init = [
        "consoleapp_init" ]

    # Let the plugin write the HTML body
    plugins.console.present(req)
