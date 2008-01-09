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

# action=rm: Delete a file or directory (recursively).
#       path:   The path to the file or directory to delete.
# TODO: More actions.

import os
import stat
import time

import cjson
import pysvn

from common import (util, studpath)

DEFAULT_LOGMESSAGE = "No log message supplied."

# Make a Subversion client object
svnclient = pysvn.Client()

# Mime types
# application/json is the "best" content type but is not good for
# debugging because Firefox just tries to download it
mime_dirlisting = "text/plain"
#mime_dirlisting = "application/json"
mime_filedump = "text/plain"

def handle(req):
    """Handler for the File Services application."""

    # Set request attributes
    req.write_html_head_foot = False     # No HTML

    # Get all the arguments, if POST.
    # Ignore arguments if not POST, since we aren't allowed to cause
    # side-effects on the server.
    action = None
    fields = None
    if req.method == 'POST':
        fields = req.get_fieldstorage()
        action = fields.getfirst('action')

    if action is not None:
        handle_action(req, action, fields)

    handle_return(req)

def handle_action(req, action, fields):
    """Perform the "action" part of the response.
    This function should only be called if the response is a POST.
    This performs the action's side-effect on the server. If unsuccessful,
    writes the X-IVLE-Action-Error header to the request object. Otherwise,
    does not touch the request object. Does NOT write any bytes in response.

    action: String, the action requested. Not sanitised.
    fields: FieldStorage object containing all arguments passed.
    """
    if action == "rm":
        path = fields.getfirst('path')
        # TODO: Delete the file
        # Do an SVN rm if possible
        pass

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
        # TODO: Known bug:
        # Fatal error if any file is missing (deleted with rm instead of svn
        # rm)
        # Handle gracefully.
        try:
            status_list = svnclient.status(path, recurse=False, get_all=True,
                            update=False)
            list = filter(lambda x: x != None,
                map(PysvnStatus_to_fileinfo(path), status_list))
        except pysvn.ClientError:
            # Presumably the directory is not under version control.
            # Fallback to just an OS file listing.
            filenames = os.listdir(path)
            list = map(file_to_fileinfo(path), filenames)

        req.write(cjson.encode(list))
    else:
        # It's a file. Return the file contents.
        req.content_type = mime_filedump
        req.headers_out['X-IVLE-Return'] = 'File'

        req.sendfile(path)

def file_to_fileinfo(path):
    """Given a filename (relative to a given path), gets all the info "ls"
    needs to display about the filename. Returns a dict mapping a number of
    fields which are returned."""
    # Note: curried so it can be used with map
    def ftf(filename):
        fullpath = os.path.join(path, filename)
        d = {"filename" : filename}
        file_stat = os.stat(fullpath)
        d["isdir"] = stat.S_ISDIR(file_stat.st_mode)
        d["size"] = file_stat.st_size
        d["mtime"] = time.ctime(file_stat.st_mtime)
        return d
    return ftf

def PysvnStatus_to_fileinfo(path):
    """Given a PysvnStatus object, gets all the info "ls"
    needs to display about the filename. Returns a dict mapping a number of
    fields which are returned.

    May return None.
    """
    # Note: curried so it can be used with map
    path = os.path.normcase(path)
    def ftf(status):
        fullpath = status.path
        # For some reason it returns the dir itself. Exclude that.
        if path == os.path.normcase(fullpath):
            return None
        d = {"filename" : os.path.basename(fullpath)}
        text_status = status.text_status
        d["svnstatus"] = str(text_status)
        try:
            file_stat = os.stat(fullpath)
            d["isdir"] = stat.S_ISDIR(file_stat.st_mode)
            d["size"] = file_stat.st_size
            d["mtime"] = time.ctime(file_stat.st_mtime)
        except OSError:
            # Here if, eg, the file is missing.
            # Can't get any more information so just return d
            pass
        return d
    return ftf

