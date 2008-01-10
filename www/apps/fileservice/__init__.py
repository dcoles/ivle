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

# App: File Service (AJAX server)
# Author: Matt Giuca
# Date: 9/1/2008

# This application is an AJAX service. Receives file handling instructions as
# requests. Performs actions on the student's workspace, and returns directory
# listings in JSON.

# This rather large documentation explains the request and response to the
# file service app (it should probably be taken to a separate document).

# This is not intended to be accessed directly by the user. It is targeted by
# AJAX calls in applications such as browser and editor.

# Application usage: The input to the application is determined by the fields
# passed in as HTTP variables (either in the URL or message body). Also, in
# keeping with REST, actions only take effect if this is a POST request as
# opposed to a GET request (although a GET request is still allowed to just
# get a listing or file dump). Also, the "path" (the part of the URL
# after "fileservice" and before the GET variables) is taken into account.

# Aside from the side-effects to the server (note: side-effects are only
# possible for POST requests), the response takes two parts. The response
# header contains information about success or failure of the operation. The
# response body may contain the requested file.

# Fileservice has two separate roles: First, an action is performed. This may
# be a copy, write, or svn up operation. Then, a file or directory listing is
# returned. This directory listing may be completely separate from the action,
# but they are performed together because the client will usually want to
# perform some action, then update its display as a result of the action.

# GET requests will have all variables ignored, and the only behaviour will be
# to generate the directory or file listing. POST requests will result in an
# action if one is specified. If the action is UNSUCCESSFUL, returns the
# header "X-IVLE-Action-Error: <errormessage>". Successful actions succeed
# silently. Note that the action does not affect the HTTP response code (it
# may be 200 even upon failure).

# The path (req.path) controls which file or directory will be
# returned. If it is a file, returns the header "X-IVLE-Return: File" and
# status 200 OK. The response body is a verbatim dump of the file specified.
# The Content-Type will probably be text/plain but should not be relied upon.
# If it is a directory, returns the header "X-IVLE-Return: Dir" and status
# 200 OK. The response body is a JSON directory listing (see below). The
# Content-Type cannot be relied upon. If the file is not found or there is
# some other read error, returns no X-IVLE-Return header, a 400-level
# response status. (404 File Not Found, 403 Forbidden, etc), and a header
# "X-IVLE-Return-Error: <errormessage>".

### Actions ###

# The most important argument is "action". This determines which action is
# taken. Note that action, and all other arguments, are ignored unless the
# request is a POST request. The other arguments depend upon the action.
# Note that paths are often specified as arguments. Paths that begin with a
# slash are taken relative to the user's home directory (the top-level
# directory seen when fileservice has no arguments or path). Paths without a
# slash are taken relative to the specified path.

# action=remove: Delete a file(s) or directory(s) (recursively).
#       path:   The path to the file or directory to delete. Can be specified
#               multiple times.
# TODO: More actions.

import os
import stat
import time
import mimetypes

import cjson
import pysvn

from common import (util, studpath)
import conf.mimetypes

DEFAULT_LOGMESSAGE = "No log message supplied."

# Make a Subversion client object
svnclient = pysvn.Client()

# Mime types
# application/json is the "best" content type but is not good for
# debugging because Firefox just tries to download it
mime_dirlisting = "text/html"
#mime_dirlisting = "application/json"

class ActionError(Exception):
    """Represents an error processing an action. This can be
    raised by any of the action functions, and will be caught
    by the top-level handler, put into the HTTP response field,
    and continue.

    Important Security Consideration: The message passed to this
    exception will be relayed to the client.
    """
    pass

def handle(req):
    """Handler for the File Services application."""

    # Set request attributes
    req.write_html_head_foot = False     # No HTML

    # Get all the arguments, if POST.
    # Ignore arguments if not POST, since we aren't allowed to cause
    # side-effects on the server.
    action = None
    fields = None
    if True or req.method == 'POST':
        fields = req.get_fieldstorage()
        action = fields.getfirst('action')

    if action is not None:
        try:
            handle_action(req, action, fields)
        except ActionError, message:
            req.headers_out['X-IVLE-Action-Error'] = str(message)

    handle_return(req)

def handle_action(req, action, fields):
    """Perform the "action" part of the response.
    This function should only be called if the response is a POST.
    This performs the action's side-effect on the server. If unsuccessful,
    writes the X-IVLE-Action-Error header to the request object. Otherwise,
    does not touch the request object. Does NOT write any bytes in response.

    May throw an ActionError. The caller should put this string into the
    X-IVLE-Action-Error header, and then continue normally.

    action: String, the action requested. Not sanitised.
    fields: FieldStorage object containing all arguments passed.
    """
    if action == "remove":
        path = fields.getlist('path')
        action_remove(req, path)
    else:
        # Default, just send an error but then continue
        raise ActionError("Unknown action")

def handle_return(req):
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

### ACTIONS ###

def actionpath_to_local(req, path):
    """Determines the local path upon which an action is intended to act.
    Note that fileservice actions accept two paths: the request path,
    and the "path" argument given to the action.
    According to the rules, if the "path" argument begins with a '/' it is
    relative to the user's home; if it does not, it is relative to the
    supplied path.

    This resolves the path, given the request and path argument.

    May raise an ActionError("Invalid path"). The caller is expected to
    let this fall through to the top-level handler, where it will be
    put into the HTTP response field. Never returns None.
    """
    if path is None:
        path = req.path
    elif len(path) > 0 and path[0] == os.sep:
        # Relative to student home
        path = path[1:]
    else:
        # Relative to req.path
        path = os.path.join(req.path, path)

    _, r = studpath.url_to_local(path)
    if r is None:
        raise ActionError("Invalid path")
    return r

def action_remove(req, paths):
    # TODO: Do an SVN rm if the file is versioned.
    """Removes a list of files or directories."""
    goterror = False
    for path in paths:
        path = actionpath_to_local(req, path)
        try:
            os.remove(path)
        except OSError:
            goterror = True
    if goterror:
        if len(paths) == 1:
            raise ActionError("Could not delete the file specified")
        else:
            raise ActionError(
                "Could not delete one or more of the files specified")
