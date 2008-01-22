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
import pwd

import cjson

from common import (util, studpath)
import conf

trampoline_path = os.path.join(conf.ivle_install_dir, "bin/trampoline")
python_path = "/usr/bin/python"                     # Within jail
console_dir = "/opt/ivle/console"                   # Within jail
console_path = "/opt/ivle/console/python-console"   # Within jail

def handle(req):
    """Handler for the Console Service AJAX backend application."""
    if len(req.path) > 0 and req.path[-1] == os.sep:
        path = req.path[:-1]
    else:
        path = req.path
    # The path determines which "command" we are receiving
    if req.path == "start":
        handle_start(req)
    elif req.path == "chat":
        handle_chat(req)
    else:
        req.throw_error(req.HTTP_BAD_REQUEST)

def handle_start(req):
    jail_path = os.path.join(conf.jail_base, req.username)
    working_dir = os.path.join("/home", req.username)   # Within jail

    # Get the UID of the logged-in user
    try:
        (_,_,uid,_,_,_,_) = pwd.getpwnam(req.username)
    except KeyError:
        # The user does not exist. This should have already failed the
        # previous test.
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR)

    # Set request attributes
    req.content_type = "text/plain"
    req.write_html_head_foot = False

    # TODO: Figure out the host name the console server is running on.
    host = req.hostname

    # Find an available port on the server.
    # TODO
    port = 1025

    # Create magic
    # TODO
    magic = "xyzzy"

    # Start the console server (port, magic)
    # trampoline usage: tramp uid jail_dir working_dir script_path args
    # console usage:    python-console port magic
    # TODO: Cleanup (don't use os.system)
    # TODO: Pass working_dir as argument, let console cd to it
    # Use "&" to run as a background process
    cmd = ' '.join([trampoline_path, str(uid), jail_path, console_dir,
        python_path, console_path, str(port), str(magic), "&"])
    #req.write(cmd + '\n')
    os.system(cmd)

    # Return port, magic
    req.write(cjson.encode({"host": host, "port": port, "magic": magic}))

def handle_chat(req):
    req.throw_error(req.HTTP_NOT_IMPLEMENTED)
