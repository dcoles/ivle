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

# Module: common.util
# Author: Matt Giuca
# Date: 12/12/2007

# Contains common utility functions.
# Also initialises mime types library. You must import util before using
# Python's builtin mimetypes module to make sure local settings are applied.

import os
import mimetypes

import conf
import conf.mimetypes

root_dir = conf.root_dir

class IVLEError(Exception):
    """
    This is the "standard" exception class for IVLE errors.
    It is the ONLY exception which should propagate to the top - it will then
    be displayed to the user as an HTTP error with the given code.

    All other exceptions are considered IVLE bugs and should not occur
    (they will display a traceback).

    This error should not be raised directly. Call req.throw_error.
    """
    def __init__(self, httpcode, message=None):
        self.httpcode = httpcode
        self.message = message
        self.args = (httpcode, message)

def make_path(path):
    """Given a path relative to the IVLE root, makes the path relative to the
    site root using conf.root_dir. This path can be used in URLs sent to the
    client."""
    return os.path.join(root_dir, path)

def make_local_path(path):
    """Given a path relative to the IVLE root, on the local file system, makes
    the path relative to the root using conf.ivle_install_dir. This path can
    be used in reading files from the local file system."""
    return os.path.join(conf.ivle_install_dir, 'www', path)

def unmake_path(path):
    """Given a path relative to the site root, makes the path relative to the
    IVLE root by removing conf.root_dir if it appears at the beginning. If it
    does not appear at the beginning, returns path unchanged. Also normalises
    the path."""
    path = os.path.normpath(path)
    root = os.path.normpath(root_dir)

    if path.startswith(root):
        path = path[len(root):]
        # Take out the slash as well
        if len(path) > 0 and path[0] == os.sep:
            path = path[1:]

    return path

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

# Initialise mime types library
mimetypes.init()
for (ext, mimetype) in conf.mimetypes.additional_mime_types.items():
    mimetypes.add_type(mimetype, ext)

def nice_filetype(filename):
    """Given a filename or basename, returns a "friendly" name for that
    file's type.
    eg. nice_mimetype("file.py") == "Python source code".
        nice_filetype("file.bzg") == "BZG file".
        nice_filetype("directory/") == "Directory".
    """
    if filename[-1] == os.sep:
        return "Directory"
    else:
        try:
            return conf.mimetypes.nice_mimetypes[
                mimetypes.guess_type(filename)[0]]
        except KeyError:
            filename = os.path.basename(filename)
            try:
                return filename[filename.rindex('.')+1:].upper() + " file"
            except ValueError:
                return "File"
