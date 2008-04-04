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
# Also performs common authorization, disallowing students from visiting paths
# they dont own.

import os
import stat
import pysvn

import conf
from common import util

# Make a Subversion client object (for published)
svnclient = pysvn.Client()

def url_to_local(urlpath):
    """Given a URL path (part of a URL query string, see below), returns a
    tuple of
        * the username of the student whose directory is being browsed
        * the absolute path in the file system where that file will be
            found within the student directories.

    urlpath: Part of the URL, but only the part *after* the application. For
    instance, given the URL "/ivle/browse/joe/mydir/myfile", urlpath will
    be just "joe/mydir/myfile". The expected result is something like
    ("joe", "/home/informatics/jails/joe/home/joe/mydir/myfile").
    Note that the actual location is not guaranteed by this interface (this
    function serves as a single point of control as to how URLs map onto
    student directories).

    Returns (None, None) if the path is empty.

    See also: conf.jail_base
    """
    # First normalise the path
    urlpath = os.path.normpath(urlpath)
    # Now if it begins with ".." or separator, then it's illegal
    if urlpath.startswith("..") or urlpath.startswith(os.sep):
        return (None, None)
    # Note: User can be a group name. There is absolutely no difference in our
    # current directory scheme.
    (user, subpath) = util.split_path(urlpath)
    if user is None: return (None, None)

    # Join the user onto 'home' then the full path specified.
    # This results in the user's name being repeated twice, which is in
    # accordance with our directory scheme.
    # (The first time is the name of the jail, the second is the user's home
    # directory within the jail).
    path = os.path.join(conf.jail_base, user, 'home', urlpath)

    return (user, path)

def url_to_jailpaths(urlpath):
    """Given a URL path (part of a URL query string), returns a tuple of
        * the username of the student whose directory is being browsed
        * the absolute path where the jail will be located.
        * the path of the file relative to the jail.

    urlpath: See urlpath in url_to_local.

    >>> url_to_jailpaths("joe/mydir/myfile")
    ("joe", "/home/informatics/jails/joe", "home/joe/mydir/myfile")

    >>> url_to_jailpaths("")
    (None, None, None)
    """
    # First normalise the path
    urlpath = os.path.normpath(urlpath)
    # Now if it begins with ".." then it's illegal
    if urlpath.startswith(".."):
        return (None, None, None)
    # Note: User can be a group name. There is absolutely no difference in our
    # current directory scheme.
    (user, subpath) = util.split_path(urlpath)
    if user is None: return (None, None, None)

    jail = os.path.join(conf.jail_base, user)
    path = os.path.join('/home', urlpath)

    return (user, jail, path)

def svnpublished(path):
    """Given a path on the LOCAL file system, determines whether the path has
    its "ivle:published" property active (in subversion). Returns True
    or False."""
    # Read SVN properties for this path
    try:
        props = svnclient.propget("ivle:published", path, recurse=False)
    except pysvn.ClientError:
        # Not under version control? Then it isn't published.
        return False
    return len(props) > 0

def published(path):
    """Given a path on the LOCAL file system, determines whether the path has a 
    '.published' file.  Returns True or False."""
    publish_file_path = os.path.join(path,'.published')
    return os.access(publish_file_path,os.F_OK)

def worldreadable(path):
    """Given a path on the LOCAL file system, determines whether the path is 
    world readble. Returns True or False."""
    try:
        mode = os.stat(path).st_mode
        if mode & stat.S_IROTH:
            return True
        else:
            return False
    except OSError, e:
        return False


def authorize(req):
    """Given a request, checks whether req.user is allowed to
    access req.path. Returns None on authorization success. Raises
    HTTP_FORBIDDEN on failure.

    This is for general authorization (assuming not in public mode; this is
    the standard auth code for fileservice, download and serve).
    """
    # TODO: Groups
    # First normalise the path
    urlpath = os.path.normpath(req.path)
    # Now if it begins with ".." or separator, then it's illegal
    if urlpath.startswith("..") or urlpath.startswith(os.sep):
        req.throw_error(req.HTTP_FORBIDDEN)

    (owner, _) = util.split_path(urlpath)
    if req.user.login != owner:
        req.throw_error(req.HTTP_FORBIDDEN)

def authorize_public(req):
    """A different kind of authorization. Rather than making sure the
    logged-in user owns the file, this checks if the file is in a published
    directory.

    This is for the "public mode" of the serve app.

    Same interface as "authorize" - None on success, HTTP_FORBIDDEN exception
    raised on failure.
    """
    _, path = url_to_local(req.path)
    dirpath, _ = os.path.split(path)
    if not (worldreadable(dirpath) and published(dirpath)):
        req.throw_error(req.HTTP_FORBIDDEN)
