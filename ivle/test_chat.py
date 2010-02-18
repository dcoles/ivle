from nose import with_setup
from nose.tools import assert_equal, raises

import chat
import socket

TIMEOUT = 0.1
NULLNETSTRING = "0:,"
SIMPLESTRING = "Hello world!"
SIMPLENETSTRING = "12:Hello world!,"

class TestCases(object):
    def setup(self):
        """Creates a socket pair for testing"""
        self.s1, self.s2 = socket.socketpair()
        self.s1.settimeout(TIMEOUT)
        self.s2.settimeout(TIMEOUT)

    def teardown(self):
        """Closes the socket pair"""
        self.s1.close()
        self.s2.close()

    @with_setup(setup, teardown)
    def test_send_null_netstring(self):
        """Check that we construct a empty Netstring correctly"""
        chat.send_netstring(self.s1, "")
        assert_equal(self.s2.recv(1024), NULLNETSTRING)

    @with_setup(setup, teardown)
    def test_send_simple_netstring(self):
        """Check that we construct a simple Netstring correctly"""
        chat.send_netstring(self.s1, SIMPLESTRING)
        assert_equal(self.s2.recv(1024), SIMPLENETSTRING)

    @with_setup(setup, teardown)
    def test_recv_null_netstring(self):
        """Check that we can decode a null Netstring"""
        self.s1.sendall(NULLNETSTRING)
        assert_equal(chat.recv_netstring(self.s2), "")

    @with_setup(setup, teardown)
    def test_recv_null_netstring(self):
        """Check that we can decode a simple Netstring"""
        self.s1.sendall(SIMPLENETSTRING)
        assert_equal(chat.recv_netstring(self.s2), SIMPLESTRING)

    @with_setup(setup, teardown)
    @raises(socket.timeout)
    def test_short_netstring(self):
        self.s1.sendall("1234:not that long!,")
        assert chat.recv_netstring(self.s2) is None

    @with_setup(setup, teardown)
    @raises(chat.ProtocolError)
    def test_long_netstring(self):
        self.s1.sendall("5:not that short!,")
        assert chat.recv_netstring(self.s2) is None

