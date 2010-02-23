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

# Module: studpath
# Author: Matt Giuca
# Date:   14/12/2007

# Provides functions for translating URLs into physical locations in the
# student directories in the local file system.
# Also performs common authorization, disallowing students from visiting paths
# they dont own.

import os
import stat

from ivle import util

def url_to_local(config, urlpath):
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

    >>> stubconfig = {'paths': {'jails': {'mounts': '/jails'}}}

    >>> url_to_local(stubconfig, 'joe/foo/bar/baz')
    ('joe', '/jails/joe/home/joe/foo/bar/baz')
    >>> url_to_local(stubconfig, 'joe')
    ('joe', '/jails/joe/home/joe')
    >>> url_to_local(stubconfig, 'joe/')
    ('joe', '/jails/joe/home/joe')

    We have some protection from various potential attacks. An empty,
    absolute, or ..-prefixed path yields a special result.

    >>> url_to_local(stubconfig, '')
    (None, None)
    >>> url_to_local(stubconfig, '/foo')
    (None, None)
    >>> url_to_local(stubconfig, '../bar')
    (None, None)
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
    path = os.path.join(config['paths']['jails']['mounts'],
                        user, 'home', urlpath)

    return (user, path)

def url_to_jailpaths(config, urlpath):
    """Given a URL path (part of a URL query string), returns a tuple of
        * the username of the student whose directory is being browsed
        * the absolute path where the jail will be located.
        * the path of the file relative to the jail.

    urlpath: See urlpath in url_to_local.

    >>> stubconfig = {'paths': {'jails': {'mounts': '/jails'}}}

    >>> url_to_jailpaths(stubconfig, "joe/mydir//myfile/.././myfile")
    ('joe', '/jails/joe', '/home/joe/mydir/myfile')
    >>> url_to_jailpaths(stubconfig, "")
    (None, None, None)
    >>> url_to_jailpaths(stubconfig, "../foo")
    (None, None, None)
    >>> url_to_jailpaths(stubconfig, "/foo")
    (None, None, None)
    """
    # First normalise the path
    urlpath = os.path.normpath(urlpath)
    # Now if it begins with "..", or is absolute, then it's illegal
    if urlpath.startswith("..") or os.path.isabs(urlpath):
        return (None, None, None)
    # Note: User can be a group name. There is absolutely no difference in our
    # current directory scheme.
    (user, subpath) = util.split_path(urlpath)
    if user is None: return (None, None, None)

    jail = os.path.join(config['paths']['jails']['mounts'], user)
    path = to_home_path(urlpath)

    return (user, jail, path)

def to_home_path(urlpath):
    """Given a URL path (eg. joe/foo/bar/baz), returns a path within the home.

    >>> to_home_path('joe/foo/bar/baz')
    '/home/joe/foo/bar/baz'
    >>> to_home_path('joe/foo//bar/baz/../../')
    '/home/joe/foo'
    >>> to_home_path('joe/foo//bar/baz/../../../../../') is None
    True
    """

    urlpath = os.path.normpath(urlpath)
    # If it begins with '..', it's illegal.
    if urlpath.startswith(".."):
        return None

    return os.path.join('/home', urlpath)

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


def authorize(req, user):
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
        return False

    (owner, _) = util.split_path(urlpath)
    if user.login != owner:
        return False
    return True

def authorize_public(req):
    """A different kind of authorization. Rather than making sure the
    logged-in user owns the file, this checks if the file is in a published
    directory.

    This is for the "public mode" of the serve app.

    Same interface as "authorize" - None on success, HTTP_FORBIDDEN exception
    raised on failure.
    """
    _, path = url_to_local(req.config, req.path)

    # Walk up the tree, and find the deepest directory.
    while not os.path.isdir(path):
        path = os.path.dirname(path)

    if not (worldreadable(path) and published(path)):
        return False
    return True
