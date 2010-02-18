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
import hashlib
import sys
import os
import socket
import traceback

SOCKETTIMEOUT = 60
BLOCKSIZE = 1024

class Terminate(Exception):
    """Exception thrown when server is to be shut down. It will attempt to
    send the final_response to the client and then exits"""
    def __init__(self, final_response=None):
        self.final_response = final_response

    def __str__(self):
        return repr(self.final_response)

class ProtocolError(Exception):
    """Exception thrown when client violates the the chat protocol"""
    pass

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

        si = os.open(os.devnull, os.O_RDONLY)
        os.dup2(si, sys.stdin.fileno())

        so = os.open(os.devnull, os.O_WRONLY)
        os.dup2(so, sys.stdout.fileno())

        se = os.open(os.devnull, os.O_WRONLY)
        os.dup2(se, sys.stderr.fileno())

    if initializer:
        initializer()

    while True:
        (conn, addr) = s.accept()
        conn.settimeout(SOCKETTIMEOUT)
        try:
            # Grab the input
            inp = recv_netstring(conn)
            env = cjson.decode(inp)

            # Check that the message is 
            digest = hashlib.md5(env['content'] + magic).hexdigest()
            if env['digest'] != digest:
                conn.close()
                continue

            content = cjson.decode(env['content'])

            response = handler(content)

            send_netstring(conn, cjson.encode(response))

            conn.close()

        except Terminate, t:
            # Try and send final response and then terminate
            if t.final_response:
                send_netstring(conn, cjson.encode(t.final_response))
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
            send_netstring(conn, cjson.encode(json_exc))
            conn.close()


def chat(host, port, msg, magic, decode = True):
    sok = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sok.connect((host, port))
    sok.settimeout(SOCKETTIMEOUT)
    content = cjson.encode(msg)
    digest = hashlib.md5(content + magic).hexdigest()
    env = {'digest':digest,'content':content}
    json = cjson.encode(env)

    send_netstring(sok, json)
    inp = recv_netstring(sok)

    sok.close()

    if decode:
        return cjson.decode(inp)
    else:
        return inp


def send_netstring(sok, data):
    netstring = "%d:%s,"%(len(data),data)
    sok.sendall(netstring)


def recv_netstring(sok):
    # Decode netstring
    size_buffer = []
    c = sok.recv(1)
    while c != ':':
        # Limit the Netstring to less than 10^10 bytes (~1GB).
        if len(size_buffer) >= 10:
            raise ProtocolError(
                    "Could not read Netstring size in first 9 bytes: '%s'"%(
                    ''.join(size_buffer)))
        size_buffer.append(c)
        c = sok.recv(1)
    try:
        # Message should be length plus ',' terminator
        recv_expected = int(''.join(size_buffer)) + 1
    except ValueError, e:
        raise ProtocolError("Could not decode Netstring size as int: '%s'"%(
                ''.join(size_buffer)))

    # Read data
    buf = []
    recv_data = sok.recv(min(recv_expected, BLOCKSIZE))
    recv_size = len(recv_data)
    while recv_size < recv_expected:
        buf.append(recv_data)
        recv_data = sok.recv(min(recv_expected-recv_size, 1024))
        recv_size = recv_size + len(recv_data)
    assert(recv_size == recv_expected)

    # Did we receive the correct amount?
    if recv_data[-1] != ',':
        raise ProtocolError("Netstring did not end with ','")
    buf.append(recv_data[:-1])

    return ''.join(buf)
