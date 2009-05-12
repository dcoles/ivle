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

# Module: util
# Author: Matt Giuca
# Date: 12/12/2007

# Contains common utility functions.

import os
import sys
import stat

class IVLEError(Exception):
    """Legacy general IVLE exception.

    This is the old "standard" exception class for IVLE errors. It is only
    used in fileservice, and should not be used in any new code.
    """
    def __init__(self, httpcode, message=None):
        self.httpcode = httpcode
        self.message = message
        self.args = (httpcode, message)

class IVLEJailError(Exception):
    """Exception proxying an in-jail error.

    This exception indicates an error that occurred inside an IVLE CGI script
    inside the jail. It should never be raised directly - only by the 
    interpreter.

    Information will be retrieved from it, and then treated as a normal
    error.
    """
    def __init__(self, type_str, message, info):
        self.type_str = type_str
        self.message = message
        self.info = info

class FakeObject(object):
    """ A representation of an object that can't be Pickled """
    def __init__(self, type, name, attrib={}):
        self.type = type
        self.name = name
        self.attrib = attrib

    def __repr__(self):
        return "<Fake %s %s>"%(self.type, self.name)

def split_path(path):
    """Given a path, returns a tuple consisting of the top-level directory in
    the path, and the rest of the path. Note that both items in the tuple will
    NOT begin with a slash, regardless of whether the original path did. Also
    normalises the path.

    Always returns a pair of strings, except for one special case, in which
    the path is completely empty (or just a single slash). In this case the
    return value will be (None, ''). But still always returns a pair.

    Examples:

    >>> split_path("")
    (None, '')
    >>> split_path("/")
    (None, '')
    >>> split_path("home")
    ('home', '')
    >>> split_path("home/docs/files")
    ('home', 'docs/files')
    >>> split_path("//home/docs/files")
    ('', 'home/docs/files')
    """
    path = os.path.normpath(path)
    # Ignore the opening slash
    if path.startswith(os.sep):
        path = path[len(os.sep):]
    if path == '' or path == '.':
        return (None, '')
    splitpath = path.split(os.sep, 1)
    if len(splitpath) == 1:
        return (splitpath[0], '')
    else:
        return tuple(splitpath)

def incomplete_utf8_sequence(byteseq):
    """Calculate the completeness of a UTF-8 encoded string.

    Given a UTF-8-encoded byte sequence (str), returns the number of bytes at
    the end of the string which comprise an incomplete UTF-8 character
    sequence.

    If the string is empty or ends with a complete character OR INVALID
    sequence, returns 0.
    Otherwise, returns 1-3 indicating the number of bytes in the final
    incomplete (but valid) character sequence.

    Does not check any bytes before the final sequence for correctness.

    >>> incomplete_utf8_sequence("")
    0
    >>> incomplete_utf8_sequence("xy")
    0
    >>> incomplete_utf8_sequence("xy\xc3\xbc")
    0
    >>> incomplete_utf8_sequence("\xc3")
    1
    >>> incomplete_utf8_sequence("\xbc\xc3")
    1
    >>> incomplete_utf8_sequence("xy\xbc\xc3")
    1
    >>> incomplete_utf8_sequence("xy\xe0\xa0")
    2
    >>> incomplete_utf8_sequence("xy\xf4")
    1
    >>> incomplete_utf8_sequence("xy\xf4\x8f")
    2
    >>> incomplete_utf8_sequence("xy\xf4\x8f\xa0")
    3
    """
    count = 0
    expect = None
    for b in byteseq[::-1]:
        b = ord(b)
        count += 1
        if b & 0x80 == 0x0:
            # 0xxxxxxx (single-byte character)
            expect = 1
            break
        elif b & 0xc0 == 0x80:
            # 10xxxxxx (subsequent byte)
            pass
        elif b & 0xe0 == 0xc0:
            # 110xxxxx (start of 2-byte sequence)
            expect = 2
            break
        elif b & 0xf0 == 0xe0:
            # 1110xxxx (start of 3-byte sequence)
            expect = 3
            break
        elif b & 0xf8 == 0xf0:
            # 11110xxx (start of 4-byte sequence)
            expect = 4
            break
        else:
            # Invalid byte
            return 0

        if count >= 4:
            # Seen too many "subsequent bytes", invalid
            return 0

    if expect is None:
        # We never saw a "first byte", invalid
        return 0

    # We now know expect and count
    if count >= expect:
        # Complete, or we saw an invalid sequence
        return 0
    elif count < expect:
        # Incomplete
        return count

def object_to_dict(attrnames, obj):
    """Convert an object into a dictionary.

    This takes a shallow copy of the object.

    @param attrnames: Set (or iterable) of names of attributes to be copied
                      into the dictionary. (We don't auto-lookup, because this
                      function needs to be used on magical objects).
    """
    return dict((k, getattr(obj, k))
        for k in attrnames if not k.startswith('_'))

def safe_rmtree(path, ignore_errors=False, onerror=None):
    """Recursively delete a directory tree.

    Copied from shutil.rmtree from Python 2.6, which does not follow symbolic
    links (it is otherwise unsafe to call as root on untrusted directories; do
    not use shutil.rmtree in this case, as you may be running Python 2.5).

    If ignore_errors is set, errors are ignored; otherwise, if onerror
    is set, it is called to handle the error with arguments (func,
    path, exc_info) where func is os.listdir, os.remove, or os.rmdir;
    path is the argument to that function that caused it to fail; and
    exc_info is a tuple returned by sys.exc_info().  If ignore_errors
    is false and onerror is None, an exception is raised.

    """
    if ignore_errors:
        def onerror(*args):
            pass
    elif onerror is None:
        def onerror(*args):
            raise
    try:
        if os.path.islink(path):
            # symlinks to directories are forbidden, see bug #1669
            raise OSError("Cannot call safe_rmtree on a symbolic link")
    except OSError:
        onerror(os.path.islink, path, sys.exc_info())
        # can't continue even if onerror hook returns
        return
    names = []
    try:
        names = os.listdir(path)
    except os.error, err:
        onerror(os.listdir, path, sys.exc_info())
    for name in names:
        fullname = os.path.join(path, name)
        try:
            mode = os.lstat(fullname).st_mode
        except os.error:
            mode = 0
        if stat.S_ISDIR(mode):
            safe_rmtree(fullname, ignore_errors, onerror)
        else:
            try:
                os.remove(fullname)
            except os.error, err:
                onerror(os.remove, fullname, sys.exc_info())
    try:
        os.rmdir(path)
    except os.error:
        onerror(os.rmdir, path, sys.exc_info())
