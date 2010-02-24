# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2010 The University of Melbourne
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

import socket
import os
import random

import cjson
from nose.tools import assert_equal, raises

import ivle.chat


TIMEOUT = 0.1
NULLNETSTRING = "0:,"
SIMPLESTRING = "Hello world!"
SIMPLENETSTRING = "12:Hello world!,"


class TestChat(object):
    def setUp(self):
        """Creates a socket pair for testing"""
        self.s1, self.s2 = socket.socketpair()
        self.s1.settimeout(TIMEOUT)
        self.s2.settimeout(TIMEOUT)

    def tearDown(self):
        """Closes the socket pair"""
        self.s1.close()
        self.s2.close()

    def test_send_null_netstring(self):
        """Check that we construct a empty Netstring correctly"""
        ivle.chat.send_netstring(self.s1, "")
        assert_equal(self.s2.recv(1024), NULLNETSTRING)

    def test_send_simple_netstring(self):
        """Check that we construct a simple Netstring correctly"""
        ivle.chat.send_netstring(self.s1, SIMPLESTRING)
        assert_equal(self.s2.recv(1024), SIMPLENETSTRING)

    def test_recv_null_netstring(self):
        """Check that we can decode a null Netstring"""
        self.s1.sendall(NULLNETSTRING)
        assert_equal(ivle.chat.recv_netstring(self.s2), "")

    def test_recv_null_netstring(self):
        """Check that we can decode a simple Netstring"""
        self.s1.sendall(SIMPLENETSTRING)
        assert_equal(ivle.chat.recv_netstring(self.s2), SIMPLESTRING)

    @raises(socket.timeout)
    def test_invalid_short_netstring(self):
        self.s1.sendall("1234:not that long!,")
        assert ivle.chat.recv_netstring(self.s2) is None

    @raises(ivle.chat.ProtocolError)
    def test_invalid_long_netstring(self):
        self.s1.sendall("5:not that short!,")
        assert ivle.chat.recv_netstring(self.s2) is None

    def test_long_netstring(self):
        # XXX: send() may block if this is too big
        msg = os.urandom(50000)
        ivle.chat.send_netstring(self.s1, msg)
        assert ivle.chat.recv_netstring(self.s2) == msg

    def test_multiple_netstrings(self):
        messages = []
        for i in range(10):
            message = os.urandom(random.randint(0,20))
            messages.append(message)
            ivle.chat.send_netstring(self.s1, message)
        for i in range(10):
            assert_equal(ivle.chat.recv_netstring(self.s2), messages[i])

    def test_encode(self):
        """Check that we correctly encode a basic object
        """
        MESSAGE = {}
        MAGIC = "3EE"
        content = cjson.encode(MESSAGE)
        # Digest can be formed with `echo -n "${content}${MAGIC}" | md5sum`
        DIGEST = '2b59b68e1ac0852b87fb7e64946f2658'
        expected = {'digest': DIGEST,
                'content': content}
        encoded = ivle.chat.encode(MESSAGE, MAGIC)
        assert_equal(cjson.decode(encoded), expected)

    def test_encode_decode(self):
        """Check that a round trip encoding and decoding works
        """
        MESSAGE = {'message': 'Hello, world'}
        MAGIC = "MagicString"
        encoded = ivle.chat.encode(MESSAGE, MAGIC)
        decoded = ivle.chat.decode(encoded, MAGIC)
        assert_equal(decoded, MESSAGE)

    @raises(ivle.chat.ProtocolError)
    def test_decode_bad_magic(self):
        """Check that a bad digest causes a ProtocolError to be raised
        """
        CHATMESSAGE = ('{"content": "{\\"a\\": \\"b\\"}", "digest": ' +
                '"eb860a5fe8fdbef19ffb79e3a5c47113"}')
        CORRECTMAGIC = "AEIOU"
        INCORRECTMAGIC = "ABCDE"

        # Check our "correct" string decodes without a ProtocolError
        try:
            ivle.chat.decode(CHATMESSAGE, CORRECTMAGIC)
        except ivle.chat.ProtocolError:
            raise AssertionError("ProtocolError with 'correct' magic")

        # This should raise the ProtocolError
        ivle.chat.decode(CHATMESSAGE, INCORRECTMAGIC)
