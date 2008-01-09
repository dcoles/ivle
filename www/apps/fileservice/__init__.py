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

# App: File Service (AJAX server)
# Author: Matt Giuca
# Date: 9/1/2008

# This application is an AJAX service. Receives file handling instructions as
# requests. Performs actions on the student's workspace, and returns directory
# listings in JSON.

# This is not intended to be accessed directly by the user. It is targeted by
# AJAX calls in applications such as browser and editor.

from common import util

def handle(req):
    """Handler for the Dummy application."""

    # Set request attributes
    req.content_type = "text/plain"
    req.write_html_head_foot = False     # No HTML

    # Start writing data
    # TEMP Dummy Data
    req.write('{"app": "File Service"}\n')
