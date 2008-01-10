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

# See action.py for a full description of the actions.
# See listing.py for a full description of the output format of the directory
# listing.

import os
import shutil
import stat
import time
import mimetypes

import cjson
import pysvn

from common import (util, studpath)
import conf.mimetypes

import action, listing

# Mime types
# application/json is the "best" content type but is not good for
# debugging because Firefox just tries to download it
mime_dirlisting = "text/html"
#mime_dirlisting = "application/json"

def handle(req):
    """Handler for the File Services application."""

    # Set request attributes
    req.write_html_head_foot = False     # No HTML

    # Get all the arguments, if POST.
    # Ignore arguments if not POST, since we aren't allowed to cause
    # side-effects on the server.
    act = None
    fields = None
    if req.method == 'POST':
        fields = req.get_fieldstorage()
        act = fields.getfirst('action')

    if act is not None:
        try:
            action.handle_action(req, act, fields)
        except action.ActionError, message:
            req.headers_out['X-IVLE-Action-Error'] = str(message)

    listing.handle_return(req)
