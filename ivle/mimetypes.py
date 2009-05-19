# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
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

"""MIME type utilities and constants."""

# We are named 'mimetypes', so we'd otherwise shadow the real mimetypes.
from __future__ import absolute_import

import mimetypes
import os
import os.path

DEFAULT_MIMETYPE = "text/plain"

# Mapping mime types to friendly names
NICE_MIMETYPES = {
    "text/x-python" : "Python source code",
    "text/plain" : "Text file",
    "text/html" : "HTML file",
    "image/png" : "PNG image",
}


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
            return NICE_MIMETYPES[mimetypes.guess_type(filename)[0]]
        except KeyError:
            filename = os.path.basename(filename)
            try:
                return filename[filename.rindex('.')+1:].upper() + " file"
            except ValueError:
                return "File"

