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

from common import (util, studpath, chat)
import conf
import errno

trampoline_path = os.path.join(conf.ivle_install_dir, "bin/trampoline")
python_path = "/usr/bin/python"                     # Within jail
console_dir = "/opt/ivle/scripts"                   # Within jail
console_path = "/opt/ivle/scripts/python-console"   # Within jail

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
    elif req.path == "chat":
        handle_chat(req)
    elif req.path == "block":
        handle_chat(req, kind="block")
    else:
        req.throw_error(req.HTTP_BAD_REQUEST)

def handle_start(req):
    jail_path = os.path.join(conf.jail_base, req.user.login)
    working_dir = os.path.join("/home", req.user.login)   # Within jail

    # Get the UID of the logged-in user
    uid = req.user.unixid

    # Set request attributes
    req.content_type = "text/plain"
    req.write_html_head_foot = False

    # Start the server
    (host, port, magic) = start_console(uid, jail_path, working_dir)

    # Assemble the key and return it.
    key = cjson.encode({"host": host, "port": port, "magic": magic})
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
        text = fields.getfirst("text").value
    except AttributeError:
        text = ""

    msg = {'cmd':kind, 'text':text}
    try:
        response = chat.chat(host, port, msg, magic, decode = False)
    except socket.error, (enumber, estring):
        if enumber == errno.ECONNREFUSED:
            # Timeout: Restart the session
            jail_path = os.path.join(conf.jail_base, req.user.login)
            working_dir = os.path.join("/home", req.user.login)   # Within jail
            
            # Get the UID of the logged-in user
            uid = req.user.unixid

            # Start the console
            (host, port, magic) = start_console(uid, jail_path, working_dir)

            # Make a JSON object to tell the browser to restart its console 
            # client
            new_key = cjson.encode(
                {"host": host, "port": port, "magic": magic})
            json_restart = {
                "restart": "The IVLE console has timed out due to inactivity",
                "key": new_key.encode("hex"),
            }
            response = cjson.encode(json_restart)
        else:
            # Some other error - probably serious
            raise socket.error, (enumber, estring)

    req.content_type = "text/plain"
    req.write(response)

def start_console(uid, jail_path, working_dir):
    """Starts up a console service for user uid, inside chroot jail jail_path 
    with work directory of working_dir
    Returns a tupple (host, port, magic)
    """

    # TODO: Figure out the host name the console server is running on.
    host = socket.gethostname()

    # Create magic
    # TODO
    magic = md5.new(uuid.uuid4().bytes).digest().encode('hex')

    # Try to find a free port on the server.
    # Just try some random ports in the range [3000,8000)
    # until we either succeed, or give up. If you think this
    # sounds risky, it isn't:
    # For N ports (e.g. 5000) with k (e.g. 100) in use, the
    # probability of failing to find a free port in t (e.g. 5) tries
    # is (k / N) ** t (e.g. 3.2*10e-9).

    tries = 0
    while tries < 5:
        port = int(random.uniform(3000, 8000))

        # Start the console server (port, magic)
        # trampoline usage: tramp uid jail_dir working_dir script_path args
        # console usage:    python-console port magic
        cmd = ' '.join([trampoline_path, str(uid), jail_path,
                            console_dir, python_path, console_path,
                            str(port), str(magic), working_dir])

        res = os.system(cmd)

        if res == 0:
            # success
            break;

        tries += 1

    if tries == 5:
        raise Exception, "unable to find a free port!"

    return (host, port, magic)

