# IVLE - Informatics Virtual Learning Environment
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

# Module: Chat
# Author: Thomas Conway
# Date:   5/2/2008

import cjson
import cStringIO
import md5
import os
import socket

def start_server(port, magic, daemon_mode, handler, initializer = None):
    # Attempt to open the socket.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', port))
    s.listen(1)

    # Excellent! It worked. Let's turn ourself into a daemon,
    # then get on with the job of being a python interpreter.
    if daemon_mode:
        if os.fork():   # launch child and...
            os._exit(0) # kill off parent
        os.setsid()
        if os.fork():   # launch child and...
            os._exit(0) # kill off parent again.
        os.umask(077)

    if initializer:
        initializer()

    while True:
        (conn, addr) = s.accept()
        try:
            # Grab the input
            buf = cStringIO.StringIO()
            blk = conn.recv(1024)
            while blk:
                buf.write(blk)
                try:
                    blk = conn.recv(1024, socket.MSG_DONTWAIT)
                except:
                    # Exception thrown if it WOULD block (but we
                    # told it not to wait) - ie. we are done
                    blk = None
            inp = buf.getvalue()
            env = cjson.decode(inp)
            
            # Check that the message is 
            digest = md5.new(env['content'] + magic).digest().encode('hex')
            if env['digest'] != digest:
                conn.close()
                continue

            content = cjson.decode(env['content'])

            response = handler(content)

            conn.sendall(cjson.encode(response))

            conn.close()
        except Exception, e:
            conn.sendall(cjson.encode(repr(e)))
            conn.close()


def chat(host, port, msg, magic, decode = True):
    sok = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sok.connect((host, port))
    content = cjson.encode(msg)
    digest = md5.new(content + magic).digest().encode("hex")
    env = {'digest':digest,'content':content}
    sok.send(cjson.encode(env))

    buf = cStringIO.StringIO()
    blk = sok.recv(1024)
    while blk:
        buf.write(blk)
        try:
            blk = conn.recv(1024, socket.MSG_DONTWAIT)
        except:
            # Exception thrown if it WOULD block (but we
            # told it not to wait) - ie. we are done
            blk = None
    inp = buf.getvalue()
    sok.close()

    if decode:
        return cjson.decode(inp)
    else:
        return inp
