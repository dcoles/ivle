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
import datetime

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

class IVLEJailError(Exception):
    """
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

def open_exercise_file(exercisename):
    """Given an exercise name, opens the corresponding XML file for reading.
    Returns None if the exercise file was not found.
    (For tutorials / worksheets).
    """
    # First normalise the path
    exercisename = os.path.normpath(exercisename)
    # Now if it begins with ".." or separator, then it's illegal
    if exercisename.startswith("..") or exercisename.startswith(os.sep):
        exercisefile = None
    else:
        exercisefile = os.path.join(conf.exercises_base, exercisename)

    try:
        return open(exercisefile)
    except (TypeError, IOError):    # TypeError if exercisefile == None
        return None

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

def send_terms_of_service(req):
    """
    Sends the Terms of Service document to the req object.
    This consults conf to find out where the TOS is located on disk, and sends
    that. If it isn't found, it sends a generic message explaining to admins
    how to create a real one.
    """
    try:
        req.sendfile(conf.tos_path)
    except IOError:
        req.write(
"""<h1>Terms of Service</h1>
<p><b>*** SAMPLE ONLY ***</b></p>
<p>This is the text of the IVLE Terms of Service.</p>
<p>The administrator should create a license file with an appropriate
"Terms of Service" license for your organisation.</p>
<h2>Instructions for Administrators</h2>
<p>You are seeing this message because you have not configured a Terms of
Service document.</p>
<p>When you configured IVLE, you specified a path to the Terms of Service
document (this is found in <b><tt>lib/conf/conf.py</tt></b> under
"<tt>tos_path</tt>").</p>
<p>Create a file at this location; an HTML file with the appropriately-worded
license.</p>
<p>This should be a normal XHTML file, except it should not contain
<tt>html</tt>, <tt>head</tt> or <tt>body</tt> elements - it should
just be the contents of a body element (IVLE will wrap it accordingly).</p>
<p>This will automatically be used as the license text instead of this
placeholder text.</p>
""")

def parse_iso8601(str):
    """Parses ISO8601 string into a datetime object."""
    # FIXME: Terrific hack that means we only accept the format that is 
    # produced by json.js module when it encodes date objects.
    return datetime.datetime.strptime(str, "%Y-%m-%dT%H:%M:%SZ")

