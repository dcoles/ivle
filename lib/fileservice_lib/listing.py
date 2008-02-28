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
#   * published: Boolean. True if the file has ivle:published property in
#   Subversion.
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
import stat
import time
import mimetypes
import urlparse
from cgi import parse_qs

import cjson
import pysvn

from common import (util, studpath)
import conf.mimetypes

# Make a Subversion client object
svnclient = pysvn.Client()

# For time calculations
seconds_per_day = 86400 # 60 * 60 * 24
if time.daylight:
    timezone_offset = time.altzone
else:
    timezone_offset = time.timezone

# Mime types
# application/json is the "best" content type but is not good for
# debugging because Firefox just tries to download it
mime_dirlisting = "text/html"
#mime_dirlisting = "application/json"

def handle_return(req):
    """Perform the "return" part of the response.
    This function returns the file or directory listing contained in
    req.path. Sets the HTTP response code in req, writes additional headers,
    and writes the HTTP response, if any."""

    (user, jail, path) = studpath.url_to_jailpaths(req.path)

    # FIXME: What to do about req.path == ""?
    # Currently goes to 403 Forbidden.
    urlpath = urlparse.urlparse(path)
    path = urlpath[2]
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
        req.write(cjson.encode(get_dirlisting(req, svnclient, path)))
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

def get_dirlisting(req, svnclient, path):
    """Given a local absolute path, creates a directory listing object
    ready to be JSONized and sent to the client.

    req: Request object. Will not be mutated; just reads the session.
    svnclient: Svn client object.
    path: String. Absolute path on the local file system. Not checked,
        must already be guaranteed safe.
    """
    # Are we in 'revision mode' - has someone sent the 'r' query
    # Work out the revisions from query
    revision = None

    r_str = req.get_fieldstorage().getfirst("r")

    if r_str is None:
        pass
    elif r_str == "HEAD":
        revision = pysvn.Revision( pysvn.opt_revision_kind.head )
    elif r_str == "WORKING":
        revision = pysvn.Revision( pysvn.opt_revision_kind.working )
    elif r_str == "BASE":
        revision = pysvn.Revision( pysvn.opt_revision_kind.base )
    else:
        # Is it a number?
        try:
            r = int(r_str)
            revision = pysvn.Revision( pysvn.opt_revision_kind.number, r)
        except:
            pass

    # Start by trying to do an SVN status, so we can report file version
    # status
    listing = {}
    try:
        if revision:
            ls_list = svnclient.list(path, revision=revision, recurse=False)
            for ls in ls_list:
                filename, attrs = PysvnList_tofileinfo(path, ls)
                listing[filename] = attrs
        else:
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
        mtime = os.path.getmtime(path)
        listing["."] = {"isdir" : True,
            "mtime" : mtime, "mtime_nice" : make_date_nice(mtime),
            "mtime_short" : make_date_nice_short(mtime),
            "type_nice" : util.nice_filetype("/")}

    # Listing is a nested object inside the top-level JSON.
    listing = {"listing" : listing}

    # The other object is the clipboard, if present in the browser session.
    # This can go straight from the session to JSON.
    session = req.get_session()
    if session and 'clipboard' in session:
        # In CGI mode, we can't get our hands on the
        # session (for the moment), so just leave it out.
        listing['clipboard'] = session['clipboard']
    
    return listing

def file_to_fileinfo(path, filename):
    """Given a filename (relative to a given path), gets all the info "ls"
    needs to display about the filename. Returns a dict containing a number
    of fields related to the file (excluding the filename itself)."""
    fullpath = os.path.join(path, filename)
    d = {}
    file_stat = os.stat(fullpath)
    if stat.S_ISDIR(file_stat.st_mode):
        d["isdir"] = True
        d["type_nice"] = util.nice_filetype("/")
    else:
        d["isdir"] = False
        d["size"] = file_stat.st_size
        (type, _) = mimetypes.guess_type(filename)
        if type is None:
            type = conf.mimetypes.default_mimetype
        d["type"] = type
        d["type_nice"] = util.nice_filetype(filename)
    d["mtime"] = file_stat.st_mtime
    d["mtime_nice"] = make_date_nice(file_stat.st_mtime)
    d["mtime_short"] = make_date_nice_short(file_stat.st_mtime)
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
            d["type_nice"] = util.nice_filetype("/")
            # Only directories can be published
            d["published"] = studpath.published(fullpath)
        else:
            d["isdir"] = False
            d["size"] = file_stat.st_size
            (type, _) = mimetypes.guess_type(fullpath)
            if type is None:
                type = conf.mimetypes.default_mimetype
            d["type"] = type
            d["type_nice"] = util.nice_filetype(filename)
        d["mtime"] = file_stat.st_mtime
        d["mtime_nice"] = make_date_nice(file_stat.st_mtime)
        d["mtime_short"] = make_date_nice_short(file_stat.st_mtime)
    except OSError:
        # Here if, eg, the file is missing.
        # Can't get any more information so just return d
        pass
    return filename, d

def PysvnList_tofileinfo(path, list):
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
        #    raise pysvn.ClientError
        # We actually want to return "." because we want its
        # subversion status.
        filename = "."
    else:
        filename = os.path.basename(fullpath)
    d = {}
    d["svnstatus"] = "revision" # A special status

    if pysvnlist.kind == pysvn.node_kind.dir:
        d["isdir"] = True
        d["type_nice"] = util.nice_filetype("/")
        # Only directories can be published
        #d["published"] = studpath.published(fullpath)
    else:
        d["isdir"] = False
        d["size"] = pysvnlist.size
        (type, _) = mimetypes.guess_type(fullpath)
        if type is None:
            type = conf.mimetypes.default_mimetype
        d["type"] = type
        d["type_nice"] = util.nice_filetype(filename)
        d["mtime"] = pysvnlist.time
        d["mtime_nice"] = make_date_nice(pysvnlist.time)
        d["mtime_short"] = make_date_nice_short(pysvnlist.time)

    return filename, d

def make_date_nice(seconds_since_epoch):
    """Given a number of seconds elapsed since the epoch,
    generates a string representing the date/time in human-readable form.
    "ddd mmm dd, yyyy h:m a"
    """
    #return time.ctime(seconds_since_epoch)
    return time.strftime("%a %b %d %Y, %I:%M %p",
        time.localtime(seconds_since_epoch))

def make_date_nice_short(seconds_since_epoch):
    """Given a number of seconds elapsed since the epoch,
    generates a string representing the date in human-readable form.
    Does not include the time.
    This function generates a very compact representation."""
    # Use a "naturalisation" algorithm.
    days_ago = (int(time.time() - timezone_offset) / seconds_per_day
        - int(seconds_since_epoch - timezone_offset) / seconds_per_day)
    if days_ago <= 5:
        # Dates today or yesterday, return "today" or "yesterday".
        if days_ago == 0:
            return "Today"
        elif days_ago == 1:
            return "Yesterday"
        else:
            return str(days_ago) + " days ago"
        # Dates in the last 5 days, return "n days ago".
    # Other dates, return a short date format.
    # If within the same year, omit the year (mmm dd)
    if time.localtime(seconds_since_epoch).tm_year==time.localtime().tm_year:
        return time.strftime("%b %d", time.localtime(seconds_since_epoch))
    # Else, include the year (mmm dd, yyyy)
    else:
        return time.strftime("%b %d, %Y", time.localtime(seconds_since_epoch))
