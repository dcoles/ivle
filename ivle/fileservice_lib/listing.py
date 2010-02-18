# IVLE
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

# Module: File Service / Listing
# Author: Matt Giuca
# Date: 10/1/2008

# Handles the return part of the 2-stage process of fileservice. This
# is both the directory listing, and the raw serving of non-directory files.

# File Service Format.
# If a non-directory file is requested, then the HTTP response body will be
# the verbatim bytes of that file (if the file is valid). The HTTP response
# headers will include the guessed content type of the file, and the header
# "X-IVLE-Return: File".

# Directory Listing Format.
# If the path requested is a directory, then the HTTP response body will be
# a valid JSON string describing the directory. The HTTP response headers
# will include the header "X-IVLE-Return: Dir".
#
# The JSON structure is as follows:
# * The top-level value is an object. It always contains the key "listing",
# whose value is the primary listing object. It may also contain a key
# "clipboard" which contains the clipboard object.
# * The value for "listing" is an object, with one member for each file in the
#   directory, plus an additional member (key ".") for the directory itself.
# * Each member's key is the filename. Its value is an object, which has
#   various members describing the file.
# The members of this object are as follows:
#   * svnstatus: String. The svn status of the file. Either all files in a
#   directory or no files have an svnstatus. String may take the values:
#   - none - does not exist
#   - unversioned - is not a versioned thing in this wc
#   - normal - exists, but uninteresting.
#   - added - is scheduled for addition
#   - missing - under v.c., but is missing
#   - deleted - scheduled for deletion
#   - replaced - was deleted and then re-added
#   - modified - text or props have been modified
#   - merged - local mods received repos mods
#   - conflicted - local mods received conflicting repos mods
#   - ignored - a resource marked as ignored
#   - obstructed - an unversioned resource is in the way of the versioned resource
#   - external - an unversioned path populated by an svn:external property
#   - incomplete - a directory doesn't contain a complete entries list
#   (From pysvn)
#   If svnstatus is "Missing" then the file has no other attributes.
#   * published: Boolean. True if the file is published. (Marked by a
#       .published file in the folder)
#   * isdir: Boolean. True if the file is a directory. Always present unless
#   svnstatus is "missing".
#   * size: Number. Size of the file in bytes. Present for non-directory
#   files.
#   * type: String. Guessed mime type of the file. Present for non-directory
#   files.
#   * mtime: Number. Number of seconds elapsed since the epoch.
#   The epoch is not defined (this is an arbitrary number used for sorting
#   dates).
#   * mtime_nice: String. Modification time of the file or directory. Always
#   present unless svnstatus is "Missing". Human-friendly.
#
# Members are not guaranteed to be present - client code should always check
# for each member that it is present, and handle gracefully if a member is not
# present.
#
# The listing object is guaranteed to have a "." key. Use this key to
# determine whether the directory is under version control or not. If this
# member does NOT have a "svnstatus" key, or "svnstatus" is "unversioned",
# then the directory is not under revision control (and no other files will
# have "svnstatus" either).
#
# The top-level object MAY contain a "clipboard" key, which specifies the
# files copied to the clipboard. This can be used by the client to show the
# user what files will be pasted. At the very least, the client should take
# the presence or absence of a "clipboard" key as whether to grey out the
# "paste" button.
#
# The "clipboard" object has three members:
#   * mode: String. Either "copy" or "cut".
#   * base: String. Path relative to the user's root. The common path between
#   the files.
#   * files: Array of Strings. Each element is a filename relative to base.
#   Base and files exactly correspond to the listing path and argument paths
#   which were supplied during the last copy or cut request.

import os
import sys
import stat
import mimetypes
import urlparse
from cgi import parse_qs

import cjson
import pysvn

import ivle.svn
import ivle.date
import ivle.mimetypes
from ivle import studpath

# Make a Subversion client object
svnclient = pysvn.Client()

# Whether or not to ignore dot files.
# TODO check settings!
ignore_dot_files = True

# Mime types
# application/json is the "best" content type but is not good for
# debugging because Firefox just tries to download it
mime_dirlisting = "text/plain"
#mime_dirlisting = "application/json"

# Indicates that a directory is unversioned
class UnversionedDir(Exception):
    pass

def handle_return(req, return_contents):
    """
    Perform the "return" part of the response.
    This function returns the file or directory listing contained in
    req.path. Sets the HTTP response code in req, writes additional headers,
    and writes the HTTP response, if any.

    If return_contents is True, and the path is a non-directory, returns the
    contents of the file verbatim. If False, returns a directory listing
    with a single file, ".", and info about the file.

    If the path is a directory, return_contents is ignored.
    """

    path = studpath.to_home_path(req.path)

    # FIXME: What to do about req.path == ""?
    # Currently goes to 403 Forbidden.
    urlpath = urlparse.urlparse(path)
    path = urlpath[2]
    json = None
    if path is None:
        req.status = req.HTTP_FORBIDDEN
        req.headers_out['X-IVLE-Return-Error'] = 'Forbidden'
        req.write("Forbidden")
        return

    # If this is a repository-revision request, it needs to be treated
    # differently than if it were a regular file request.
    # Note: If there IS a revision requested but the file doesn't exist in
    # that revision, this will terminate.
    revision = _get_revision_or_die(req, svnclient, path)

    if revision is None:
        if not os.access(path, os.R_OK):
            req.status = req.HTTP_NOT_FOUND
            req.headers_out['X-IVLE-Return-Error'] = 'File not found'
            req.write("File not found")
            return
        is_dir = os.path.isdir(path)
    else:
        is_dir = ivle.svn.revision_is_dir(svnclient, path, revision)

    if is_dir:
        # It's a directory. Return the directory listing.
        req.content_type = mime_dirlisting
        req.headers_out['X-IVLE-Return'] = 'Dir'
        # TODO: Fix this dirty, dirty hack
        newjson = get_dirlisting(req, svnclient, path, revision)
        if ("X-IVLE-Action-Error" in req.headers_out):
            newjson["Error"] = req.headers_out["X-IVLE-Action-Error"]
        req.write(cjson.encode(newjson))
    elif return_contents:
        # It's a file. Return the file contents.
        # First get the mime type of this file
        (type, _) = mimetypes.guess_type(path)
        if type is None:
            type = ivle.mimetypes.DEFAULT_MIMETYPE
        req.content_type = type
        req.headers_out['X-IVLE-Return'] = 'File'

        send_file(req, svnclient, path, revision)
    else:
        # It's a file. Return a "fake directory listing" with just this file.
        req.content_type = mime_dirlisting
        req.headers_out['X-IVLE-Return'] = 'File'
        req.write(cjson.encode(get_dirlisting(req, svnclient, path,
                                              revision)))

def _get_revision_or_die(req, svnclient, path):
    """Looks for a revision specification in req's URL.
    Errors and terminates the request if the specification was bad, or it
    doesn't exist for the given path.
    @param req: Request object.
    @param svnclient: pysvn Client object.
    @param path: Path to the file whose revision is to be retrieved.
    @returns: pysvn Revision object, for the file+revision specified, or None
        if there was no revision specified.
    """
    # Work out the revisions from query
    r_str = req.get_fieldstorage().getfirst("r")
    revision = ivle.svn.revision_from_string(r_str)

    # Was some revision specified AND (it didn't resolve OR it was nonexistent)
    if r_str and not (revision and
                      ivle.svn.revision_exists(svnclient, path, revision)):
        req.status = req.HTTP_NOT_FOUND
        message = ('Revision not found or file not found in revision %d' %
                   revision.number)
        req.headers_out['X-IVLE-Return-Error'] = message
        req.ensure_headers_written()
        req.write(message)
        req.flush()
        sys.exit()
    return revision

def send_file(req, svnclient, path, revision):
    """Given a local absolute path to a file, sends the contents of the file
    to the client.

    @param req: Request object. Will not be mutated; just reads the session.
    @param svnclient: Svn client object.
    @param path: String. Absolute path on the local file system. Not checked,
        must already be guaranteed safe. May be a file or a directory.
    @param revision: pysvn Revision object for the given path, or None.
    """
    if revision:
        req.write(svnclient.cat(path, revision=revision))
    else:
        req.sendfile(path)

def get_dirlisting(req, svnclient, path, revision):
    """Given a local absolute path, creates a directory listing object
    ready to be JSONized and sent to the client.

    @param req: Request object. Will not be mutated; just reads the session.
    @param svnclient: Svn client object.
    @param path: String. Absolute path on the local file system. Not checked,
        must already be guaranteed safe. May be a file or a directory.
    @param revision: pysvn Revision object for the given path, or None.
    """

    # Start by trying to do an SVN status, so we can report file version
    # status
    listing = {}
    svnclient.exception_style = 1       # Get rich exceptions
    try:
        if revision:
            ls_list = svnclient.list(path, revision=revision, recurse=False)
            for ls in ls_list:
                filename, attrs = PysvnList_to_fileinfo(path, ls)
                if isinstance(filename, str):   # Expect a unicode from pysvn
                    filename = filename.decode('utf-8')
                listing[filename] = attrs
        else:
            status_list = svnclient.status(path, recurse=False, get_all=True,
                        update=False)
            for status in status_list:
                filename, attrs = PysvnStatus_to_fileinfo(path, status)
                if isinstance(filename, str):   # Expect a unicode from pysvn
                    filename = filename.decode('utf-8')
                listing[filename] = attrs
    except (pysvn.ClientError, UnversionedDir), e:
        # Could indicate a serious SVN error, or just that the directory is
        # not under version control (which is perfectly normal).
        # Error code 155007 is "<dir> is not a working copy"
        if isinstance(e, pysvn.ClientError) and e[1][0][1] != 155007:
            # This is a serious error -- let it propagate upwards
            raise
        # The directory is not under version control.
        # Fallback to just an OS file listing.
        try:
            for filename in os.listdir(path):
                listing[filename.decode('utf-8')] = file_to_fileinfo(path, filename)[1]
                try:
                    svnclient.status(os.path.join(path, filename), recurse = False)
                    listing[filename.decode('utf-8')]['svnstatus'] = 'normal'
                except:
                    pass
        except OSError:
            # Non-directories will error - that's OK, we just want the "."
            pass
        # The subversion one includes "." while the OS one does not.
        # Add "." to the output, so the caller can see we are
        # unversioned.
        listing["."] = file_to_fileinfo(path, "")[1]

    if ignore_dot_files:
        for fn in listing.keys():
            if fn != "." and fn.startswith("."):
                del listing[fn]

    # Listing is a nested object inside the top-level JSON.
    listing = {"listing" : listing}

    if revision:
        listing['revision'] = revision.number

    # The other object is the clipboard, if present in the browser session.
    # This can go straight from the session to JSON.
    session = req.get_session()
    if session and 'clipboard' in session:
        # In CGI mode, we can't get our hands on the
        # session (for the moment), so just leave it out.
        listing['clipboard'] = session['clipboard']
    
    return listing

def _fullpath_stat_fileinfo(fullpath):
    if isinstance(fullpath, unicode):
        fullpath = fullpath.encode('utf-8')     # os.stat can't handle unicode
    file_stat = os.stat(fullpath)
    return _stat_fileinfo(fullpath, file_stat)

def _stat_fileinfo(fullpath, file_stat):
    d = {}
    if stat.S_ISDIR(file_stat.st_mode):
        d["isdir"] = True
        d["type_nice"] = ivle.mimetypes.nice_filetype("/")
        # Only directories can be published
        d["published"] = studpath.published(fullpath)
    else:
        d["isdir"] = False
        d["size"] = file_stat.st_size
        (type, _) = mimetypes.guess_type(fullpath)
        if type is None:
            type = ivle.mimetypes.DEFAULT_MIMETYPE
        d["type"] = type
        d["type_nice"] = ivle.mimetypes.nice_filetype(fullpath)
    d["mtime"] = file_stat.st_mtime
    d["mtime_nice"] = ivle.date.make_date_nice(file_stat.st_mtime)
    d["mtime_short"] = ivle.date.make_date_nice_short(file_stat.st_mtime)
    return d

def file_to_fileinfo(path, filename):
    """Given a filename (relative to a given path), gets all the info "ls"
    needs to display about the filename. Returns pair mapping filename to
    a dict containing a number of other fields."""
    fullpath = path if filename in ('', '.') else os.path.join(path, filename)
    return filename, _fullpath_stat_fileinfo(fullpath)

def PysvnStatus_to_fileinfo(path, status):
    """Given a PysvnStatus object, gets all the info "ls"
    needs to display about the filename. Returns a pair mapping filename to
    a dict containing a number of other fields."""
    path = os.path.normcase(path)
    fullpath = status.path
    # If this is "." (the directory itself)
    if path == os.path.normcase(fullpath):
        # If this directory is unversioned, then we aren't
        # looking at any interesting files, so throw
        # an exception and default to normal OS-based listing. 
        if status.text_status == pysvn.wc_status_kind.unversioned:
            raise UnversionedDir()
        # We actually want to return "." because we want its
        # subversion status.
        filename = "."
    else:
        filename = os.path.basename(fullpath)
    text_status = status.text_status
    d = {'svnstatus': str(text_status)}

    if status.entry is not None:
        d.update({
           'svnurl': status.entry.url,
           'svnrevision': status.entry.revision.number
             if status.entry.revision.kind == pysvn.opt_revision_kind.number
             else None,
        })

    try:
        d.update(_fullpath_stat_fileinfo(fullpath))
    except OSError:
        # Here if, eg, the file is missing.
        # Can't get any more information so just return d
        pass
    return filename, d

def PysvnList_to_fileinfo(path, list):
    """Given a List object from pysvn.Client.list, gets all the info "ls"
    needs to display about the filename. Returns a pair mapping filename to
    a dict containing a number of other fields."""
    path = os.path.normcase(path)
    pysvnlist = list[0]
    fullpath = pysvnlist.path
    # If this is "." (the directory itself)
    if path == os.path.normcase(fullpath):
        # If this directory is unversioned, then we aren't
        # looking at any interesting files, so throw
        # an exception and default to normal OS-based listing. 
        #if status.text_status == pysvn.wc_status_kind.unversioned:
        #    raise UnversionedDir()
        # We actually want to return "." because we want its
        # subversion status.
        filename = "."
    else:
        filename = os.path.basename(fullpath)
    d = {'svnstatus': 'revision'} # A special status.

    wrapped = ivle.svn.PysvnListStatWrapper(pysvnlist)
    d.update(_stat_fileinfo(fullpath, wrapped))

    return filename, d
