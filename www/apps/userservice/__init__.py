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

# App: userservice
# Author: Matt Giuca
# Date: 14/2/2008

import os
import sys

import cjson

from common import (util, chat)
import conf

# TODO: Config these in setup.py
USERMGT_HOST = "localhost"
USERMGT_PORT = 3000
USERMGT_MAGIC = "magicuser"

# The user must send this declaration message to ensure they acknowledge the
# TOS
USER_DECLARATION = "I accept the IVLE Terms of Service"

def handle(req):
    """Handler for the Console Service AJAX backend application."""
    if len(req.path) > 0 and req.path[-1] == os.sep:
        path = req.path[:-1]
    else:
        path = req.path
    # The path determines which "command" we are receiving
    if req.path == "createme":
        handle_createme(req)
    else:
        req.throw_error(req.HTTP_BAD_REQUEST)

def handle_createme(req):
    """Create the jail, svn, etc, for the currently logged in user (this is
    put in the queue for usermgt to do).
    This will block until usermgt returns, which could take seconds to minutes
    in the extreme. Therefore, it is designed to be called by Ajax, with a
    nice "Please wait" message on the frontend.

    This will signal that the user has accepted the terms of the license
    agreement, and will result in the user's database status being set to
    "enabled". (Note that it will be set to "pending" for the duration of the
    handling).

    As such, it takes a single POST field, "declaration", which
    must have the value, "I accept the IVLE Terms of Service".
    (Otherwise users could navigate to /userservice/createme without
    "accepting" the terms - at least this way requires them to acknowledge
    their acceptance). It must only be called through a POST request.
    """
    if req.method != "POST":
        req.throw_error(req.HTTP_BAD_REQUEST)
    fields = req.get_fieldstorage()
    try:
        declaration = fields.getfirst('declaration')
    except AttributeError:
        req.throw_error(req.HTTP_BAD_REQUEST)
    if declaration != USER_DECLARATION:
        req.throw_error(req.HTTP_BAD_REQUEST)

    # Get the arguments for usermgt.create_user from the session
    # (The user must have already logged in to use this app)
    session = req.get_session()
    args = {
        "username": session['login_name'],
        "uid": session['unixid'],
    }
    msg = {'create_user': args}

    response = chat.chat(USERMGT_HOST, USERMGT_PORT, msg, USERMGT_MAGIC,
        decode = False)
    req.content_type = "text/plain"
    req.write(response)

