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

import os
import socket

import cjson
import errno

import ivle.console
import ivle.chat
from ivle.webapp.base.rest import JSONRESTView, named_operation
from ivle.webapp.errors import BadRequest

# XXX: Should be RPC view, with actions in URL?
class ConsoleServiceRESTView(JSONRESTView):
    '''An RPC interface to a Python console.'''
    def get_permissions(self, user, config):
        if user is not None:
            return set(['use'])
        else:
            return set()

    @named_operation('use')
    def start(self, req, cwd=''):
        working_dir = os.path.join("/home", req.user.login, cwd)

        # Start the server
        jail_path = os.path.join(req.config['paths']['jails']['mounts'],
                                 req.user.login)
        cons = ivle.console.Console(req.config, req.user, jail_path,
                working_dir)

        # Assemble the key and return it. Yes, it is double-encoded.
        return {'key': cjson.encode({"host": cons.host,
                                     "port": cons.port,
                                     "magic": cons.magic}).encode('hex')}

    @named_operation('use')
    def chat(self, req, key, text='', cwd='', kind="chat"):
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

        jail_path = os.path.join(req.config['paths']['jails']['mounts'],
                                 req.user.login)
        # Within Jail
        working_dir = os.path.join("/home", req.user.login, cwd)

        # XXX: JSONRESTView should do this for us.
        text = text.decode('utf-8')

        msg = {'cmd':kind, 'text':text}
        try:
            try:
                json_response = ivle.chat.chat(host, port, msg, magic,decode=False)
                # Snoop the response from python-console to check that it's valid
                response = cjson.decode(json_response)
            except (cjson.DecodeError, ivle.chat.ProtocolError):
                # Could not decode the reply from the python-console server
                response = {"terminate":
                    "Communication lost"}
            if "terminate" in response:
                response = restart_console(req.config, req.user, jail_path,
                    working_dir, response["terminate"])
        except socket.error, (enumber, estring):
            if enumber == errno.ECONNREFUSED:
                # Timeout: Restart the session
                response = restart_console(req.config, req.user, jail_path,
                    working_dir,
                    "Timed out due to inactivity")
            elif enumber == errno.ECONNRESET:
                # Communication issue: Restart the session
                response = restart_console(req.config, req.user, jail_path,
                    working_dir,
                    "Connection reset")
            else:
                # Some other error - probably serious
                raise socket.error, (enumber, estring)
        return response


def restart_console(config, user, jail_path, working_dir, reason):
    """Tells the client that it must be issued a new console since the old 
    console is no longer availible. The client must accept the new key.
    Returns the JSON response to be given to the client.
    """
    # Start a new console server console
    cons = ivle.console.Console(config, user, jail_path, working_dir)

    # Make a JSON object to tell the browser to restart its console client
    new_key = cjson.encode(
        {"host": cons.host, "port": cons.port, "magic": cons.magic})

    return {"restart": reason, "key": new_key.encode("hex")}
