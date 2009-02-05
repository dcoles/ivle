# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
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

# Author: Matt Giuca, Tom Conway, Will Grant

'''Python console RPC service.

Provides an HTTP RPC interface to a Python console process.

'''

import cStringIO
import md5
import os
import random
import socket
import sys
import uuid

import cjson
import errno

from ivle import (util, studpath, chat, console)
import ivle.conf
from ivle.webapp.base.views import JSONRESTView, named_operation

# XXX: Should be RPC view, with actions in URL?
class ConsoleServiceRESTView(JSONRESTView):
    '''An RPC interface to a Python console.'''
    @named_operation
    def start(self, req, cwd=''):
        working_dir = os.path.join("/home", req.user.login, cwd)

        uid = req.user.unixid

        # Start the server
        jail_path = os.path.join(ivle.conf.jail_base, req.user.login)
        cons = console.Console(uid, jail_path, working_dir)

        # Assemble the key and return it. Yes, it is double-encoded.
        return {'key': cjson.encode({"host": cons.host,
                                     "port": cons.port,
                                     "magic": cons.magic}).encode('hex')}

    @named_operation
    def chat(self, req, key, text='', kind="chat"):
        # The request *should* have the following four fields:
        # key: Hex JSON dict of host and port where the console server lives,
        # and the secret to use to digitally sign the communication with the
        # console server.
        # text: Fields to pass along to the console server
        # It simply acts as a proxy to the console server

        try:
            keydict = cjson.decode(key.decode('hex'))
            host = keydict['host']
            port = keydict['port']
            magic = keydict['magic']
        except KeyError:
            raise BadRequest("Invalid console key.")

        jail_path = os.path.join(ivle.conf.jail_base, req.user.login)
        working_dir = os.path.join("/home", req.user.login)   # Within jail
        uid = req.user.unixid

        msg = {'cmd':kind, 'text':text}
        try:
            json_response = chat.chat(host, port, msg, magic, decode = False)

            # Snoop the response from python-console to check that it's valid
            try:
                response = cjson.decode(json_response)
            except cjson.DecodeError:
                # Could not decode the reply from the python-console server
                response = {"terminate":
                    "Communication to console process lost"}
            if "terminate" in response:
                response = restart_console(uid, jail_path, working_dir,
                    response["terminate"])
        except socket.error, (enumber, estring):
            if enumber == errno.ECONNREFUSED:
                # Timeout: Restart the session
                response = restart_console(uid, jail_path, working_dir,
                    "The IVLE console has timed out due to inactivity")
            elif enumber == errno.ECONNRESET:
                # Communication issue: Restart the session
                response = restart_console(uid, jail_path, working_dir,
                    "Connection with the console has been reset")
            else:
                # Some other error - probably serious
                raise socket.error, (enumber, estring)
        return response

def handle(req):
    """Handler for the Console Service AJAX backend application."""
    if len(req.path) > 0 and req.path[-1] == os.sep:
        path = req.path[:-1]
    else:
        path = req.path
    # The path determines which "command" we are receiving
    if req.path == "start":
        handle_start(req)
    elif req.path == "interrupt":
        handle_chat(req, kind='interrupt')
    elif req.path == "restart":
        handle_chat(req, kind='terminate')
    elif req.path == "chat":
        handle_chat(req)
    elif req.path == "block":
        handle_chat(req, kind="block")
    elif req.path == "flush":
        handle_chat(req, kind="flush")
    elif req.path == "inspect":
        handle_chat(req, kind="inspect")
    else:
        req.throw_error(req.HTTP_BAD_REQUEST)



def restart_console(uid, jail_path, working_dir, reason):
    """Tells the client that it must be issued a new console since the old 
    console is no longer availible. The client must accept the new key.
    Returns the JSON response to be given to the client.
    """
    # Start a new console server console
    cons = console.Console(uid, jail_path, working_dir)

    # Make a JSON object to tell the browser to restart its console client
    new_key = cjson.encode(
        {"host": cons.host, "port": cons.port, "magic": cons.magic})
    json_restart = {
        "restart": reason,
        "key": new_key.encode("hex"),
    }
    
    return cjson.encode(json_restart)
