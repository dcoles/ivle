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

# App: consoleservice
# Author: Matt Giuca, Tom Conway
# Date: 14/1/2008

import os

import cjson

from common import (util, studpath)
import conf

def handle(req):
    """Handler for the Console Service AJAX backend application."""

    # Set request attributes
    req.content_type = "text/plain"
    req.write_html_head_foot = False

    # TODO: Figure out the host name the console server is running on.
    host = "localhost"

    # Find an available port on the server.
    # TODO
    port = 1025

    # Create magic
    # TODO
    magic = "xyzzy"

    # Start the console server (port, magic)
    # TODO: Trampoline into the jail, and run it as a background process
    jail = os.path.join(conf.jail_base, req.username)
    console_dir = os.path.join(jail, "opt/ivle/console/")
    console_path = os.path.join(console_dir, "python-console")
    os.system("cd " + console_dir + "; "
        + console_path + " " + str(port) + " " + str(magic)
        + " > /home/mgiuca/Desktop/python_console_log 2>&1 &")

    # Return port, magic
    req.write(cjson.encode({"host": host, "port": port, "magic": magic}))
