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
import sys
import os
import socket
import traceback

class Terminate(Exception):
    """Exception thrown when server is to be shut down. It will attempt to sned 
    the final_response to the client and then exits"""
    def __init__(self, final_response=None):
        self.final_response = final_response

    def __str__(self):
        return repr(self.final_response)


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

        try:
            MAXFD = os.sysconf("SC_OPEN_MAX")
        except:
            MAXFD = 256

        # Close all file descriptors, except the socket.
        for i in xrange(MAXFD):
            if i == s.fileno():
                continue
            try:
                os.close(i)
            except OSError:
                pass

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

        except Terminate, t:
            # Try and send final response and then terminate
            if t.final_response:
                conn.sendall(cjson.encode(t.final_response))
            conn.close()
            sys.exit(0)
        except Exception:
            # Make a JSON object full of exceptional goodness
            tb_dump = cStringIO.StringIO()
            e_type, e_val, e_tb = sys.exc_info()
            traceback.print_tb(e_tb, file=tb_dump)
            json_exc = {
                "type": e_type.__name__,
                "value": str(e_val),
                "traceback": tb_dump.getvalue()
            }
            conn.sendall(cjson.encode(json_exc))
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
            blk = sok.recv(1024, socket.MSG_DONTWAIT)
        except socket.error, e:
            if e[0] != 11:
                raise
            # Exception thrown if it WOULD block (but we
            # told it not to wait) - ie. we are done
            blk = None
    inp = buf.getvalue()
    sok.close()

    if decode:
        return cjson.decode(inp)
    else:
        return inp

