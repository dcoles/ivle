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
# * The top-level value is an object, with one member for each file in the
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
#   * isdir: Boolean. True if the file is a directory. Always present unless
#   svnstatus is "missing".
#   * size: Number. Size of the file in bytes. Present for non-directory
#   files.
#   * type: String. Guessed mime type of the file. Present for non-directory
#   files.
#   * mtime: String. Modification time of the file or directory. Always
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

import os
import shutil
import stat
import time
import mimetypes

import cjson
import pysvn

from common import (util, studpath)
import conf.mimetypes

import action

# Mime types
# application/json is the "best" content type but is not good for
# debugging because Firefox just tries to download it
mime_dirlisting = "text/html"
#mime_dirlisting = "application/json"

def handle_return(req, svnclient):
    """Perform the "return" part of the response.
    This function returns the file or directory listing contained in
    req.path. Sets the HTTP response code in req, writes additional headers,
    and writes the HTTP response, if any."""

    (user, path) = studpath.url_to_local(req.path)

    # FIXME: What to do about req.path == ""?
    # Currently goes to 403 Forbidden.
    if path is None:
        req.status = req.HTTP_FORBIDDEN
        req.headers_out['X-IVLE-Return-Error'] = 'Forbidden'
        req.write("Forbidden")
    elif not os.access(path, os.R_OK):
        req.status = req.HTTP_NOT_FOUND
        req.headers_out['X-IVLE-Return-Error'] = 'File not found'
        req.write("File not found")
    elif os.path.isdir(path):
        # It's a directory. Return the directory listing.
        req.content_type = mime_dirlisting
        req.headers_out['X-IVLE-Return'] = 'Dir'
        # Start by trying to do an SVN status, so we can report file version
        # status
        listing = {}
        try:
            status_list = svnclient.status(path, recurse=False, get_all=True,
                            update=False)
            for status in status_list:
                filename, attrs = PysvnStatus_to_fileinfo(path, status)
                listing[filename] = attrs
        except pysvn.ClientError:
            # Presumably the directory is not under version control.
            # Fallback to just an OS file listing.
            for filename in os.listdir(path):
                listing[filename] = file_to_fileinfo(path, filename)
            # The subversion one includes "." while the OS one does not.
            # Add "." to the output, so the caller can see we are
            # unversioned.
            listing["."] = {"isdir" : True,
                "mtime" : time.ctime(os.path.getmtime(path))}

        req.write(cjson.encode(listing))
    else:
        # It's a file. Return the file contents.
        # First get the mime type of this file
        # (Note that importing common.util has already initialised mime types)
        (type, _) = mimetypes.guess_type(path)
        if type is None:
            type = conf.mimetypes.default_mimetype
        req.content_type = type
        req.headers_out['X-IVLE-Return'] = 'File'

        req.sendfile(path)

def file_to_fileinfo(path, filename):
    """Given a filename (relative to a given path), gets all the info "ls"
    needs to display about the filename. Returns a dict containing a number
    of fields related to the file (excluding the filename itself)."""
    fullpath = os.path.join(path, filename)
    d = {}
    file_stat = os.stat(fullpath)
    if stat.S_ISDIR(file_stat.st_mode):
        d["isdir"] = True
    else:
        d["isdir"] = False
        d["size"] = file_stat.st_size
        (type, _) = mimetypes.guess_type(filename)
        if type is None:
            type = conf.mimetypes.default_mimetype
        d["type"] = type
    d["mtime"] = time.ctime(file_stat.st_mtime)
    return d

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
            raise pysvn.ClientError
        # We actually want to return "." because we want its
        # subversion status.
        filename = "."
    else:
        filename = os.path.basename(fullpath)
    d = {}
    text_status = status.text_status
    d["svnstatus"] = str(text_status)
    try:
        file_stat = os.stat(fullpath)
        if stat.S_ISDIR(file_stat.st_mode):
            d["isdir"] = True
        else:
            d["isdir"] = False
            d["size"] = file_stat.st_size
            (type, _) = mimetypes.guess_type(fullpath)
            if type is None:
                type = conf.mimetypes.default_mimetype
            d["type"] = type
        d["mtime"] = time.ctime(file_stat.st_mtime)
    except OSError:
        # Here if, eg, the file is missing.
        # Can't get any more information so just return d
        pass
    return filename, d
