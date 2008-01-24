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

# App: tutorial
# Author: Matt Giuca
# Date: 25/1/2008

# Tutorial application.
# Displays tutorial content with editable problems, allowing students to test
# and submit their solutions to problems and have them auto-tested.

# URL syntax
# All path segments are optional (omitted path segments will show menus).
# The first path segment is the subject code.
# The second path segment is the worksheet name.

import os
import cgi

from common import util

def handle(req):
    """Handler for the Tutorial application."""

    # Set request attributes
    req.content_type = "text/html"
    req.write_html_head_foot = True     # Have dispatch print head and foot

    path_segs = req.path.split(os.sep)
    subject = None
    worksheet = None
    if len(path_segs) > 2:
        req.throw_error(req.HTTP_NOT_FOUND)
    elif len(req.path) > 0:
        subject = path_segs[0]
        if len(path_segs) == 2:
            worksheet = path_segs[1]

    if subject == None:
        handle_toplevel_menu(req)
    elif worksheet == None:
        handle_subject_menu(req, subject)
    else:
        handle_worksheet(req, subject, worksheet)

def handle_toplevel_menu(req):
    req.write("<h1>IVLE Tutorials</h1>\n")
    req.write("<p>TODO: Top-level tutorial menu</p>\n")

def handle_subject_menu(req, subject):
    req.write("<h1>IVLE Tutorials - %s</h1>\n" % cgi.escape(subject))
    req.write("<p>TODO: Subject-level menu</p>\n")

def handle_worksheet(req, subject, worksheet):
    req.write("<h1>IVLE Tutorials - %s</h1>\n<h2>%s</h2>\n"
        % (cgi.escape(subject), cgi.escape(worksheet)))
    req.write("<p>TODO: Worksheet content</p>\n")

