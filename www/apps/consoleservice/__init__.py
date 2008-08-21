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

import cStringIO
import md5
import os
import random
import socket
import sys
import uuid

import cjson

from common import (util, studpath, chat, console)
import conf
import errno

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
        handle_chat(req, kind='restart')
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

def handle_start(req):
    # Changes the state on the server - must be POST
    if req.method != "POST":
        req.throw_error(req.HTTP_BAD_REQUEST)
    
    # See if we have been given extra params
    fields = req.get_fieldstorage()
    try:
        startdir = fields.getfirst("startdir").value
        working_dir = os.path.join("/home", req.user.login, startdir)
    except AttributeError:
        working_dir = os.path.join("/home", req.user.login)

    # Get the UID of the logged-in user
    uid = req.user.unixid

    # Set request attributes
    req.content_type = "text/plain"
    req.write_html_head_foot = False

    # Start the server
    jail_path = os.path.join(conf.jail_base, req.user.login)
    cons = console.Console(uid, jail_path, working_dir)

    # Assemble the key and return it.
    key = cjson.encode(
        {"host": cons.host, "port": cons.port, "magic": cons.magic})
    req.write(cjson.encode(key.encode("hex")))

def handle_chat(req, kind = "chat"):
    # The request *should* have the following four fields:
    # host, port, magic: Host and port where the console server lives,
    # and the secret to use to digitally sign the communication with the
    # console server.
    # text: Fields to pass along to the console server
    # It simply acts as a proxy to the console server
    if req.method != "POST":
        req.throw_error(req.HTTP_BAD_REQUEST)
    jail_path = os.path.join(conf.jail_base, req.user.login)
    working_dir = os.path.join("/home", req.user.login)   # Within jail
    uid = req.user.unixid
    fields = req.get_fieldstorage()
    try:
        key = cjson.decode(fields.getfirst("key").value.decode("hex"))
        host = key['host']
        port = key['port']
        magic = key['magic']
    except AttributeError:
        # Any of the getfirsts returned None
        req.throw_error(req.HTTP_BAD_REQUEST)
    # If text is None, it was probably just an empty line
    try:
        text = fields.getfirst("text").value.decode('utf-8')
    except AttributeError:
        text = ""

    msg = {'cmd':kind, 'text':text}
    try:
        response = chat.chat(host, port, msg, magic, decode = False)
        
        # Snoop the response from python-console to check that it's valid
        try:
            decoded_response = cjson.decode(response)
        except cjson.DecodeError:
            # Could not decode the reply from the python-console server
            decoded_response = {"terminate":
                "Communication to console process lost"}
        if "terminate" in decoded_response:
            response = restart_console(uid, jail_path, working_dir,
                decoded_response["terminate"])

    except socket.error, (enumber, estring):
        if enumber == errno.ECONNREFUSED:
            # Timeout: Restart the session
            response = restart_console(uid, jail_path, working_dir,
                "The IVLE console has timed out due to inactivity")
        else:
            # Some other error - probably serious
            raise socket.error, (enumber, estring)

    req.content_type = "text/plain"
    req.write(response)

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
