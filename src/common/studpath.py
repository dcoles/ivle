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

# Module: common.studpath
# Author: Matt Giuca
# Date:   14/12/2007

# Provides functions for translating URLs into physical locations in the
# student directories in the local file system.

import os

import conf
from common import util

def url_to_local(urlpath):
    """Given a URL path (part of a URL query string, see below), returns a
    tuple of
        * the username of the student whose directory is being browsed
        * the absolute path in the file system where that file will be
            found within the student directories.

    urlpath: Part of the URL, but only the part *after* the application. For
    instance, given the URL "/ivle/browse/joe/home/mydir/myfile", urlpath will
    be just "joe/home/mydir/myfile". The expected result is something like
    ("joe", "/home/informatics/jails/joe/home/svn/mydir/myfile").
    Note that the actual location is not guaranteed by this interface (this
    function serves as a single point of control as to how URLs map onto
    student directories).

    Returns (None, None) if the path is empty.

    See also: conf.student_dir
    """
    (user, subpath) = util.split_path(urlpath)
    if user is None: return (None, None)

    # Note: For now this just re-joins user and subpath
    # But we plan to muddle this around a bit so it's good that they are
    # separated.
    path = os.path.join(conf.student_dir, user, subpath)

    return (user, path)
