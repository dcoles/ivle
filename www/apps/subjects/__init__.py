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

# App: subjects
# Author: Matt Giuca
# Date: 29/2/2008

# This is an IVLE application.
# A sample / testing application for IVLE.

import os
import urllib
import cgi

from common import util

def handle(req):
    """Handler for the Subjects application. Links to subject home pages."""

    if req.path == "":
        handle_toplevel_menu(req)
    else:
        handle_subject_page(req, req.path)

def handle_toplevel_menu(req):
    # This is represented as a directory. Redirect and add a slash if it is
    # missing.
    if req.uri[-1] != '/':
        req.throw_redirect(make_tutorial_path())

    # Get list of subjects
    # TODO: Fetch from DB. For now, just get directory listing
    try:
        subjects = os.listdir(util.make_local_path(os.path.join('media',
            'subjects')))
    except OSError:
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR,
            "There are is no subject homepages directory.")
    subjects.sort()

    req.content_type = "text/html"
    req.write_html_head_foot = True
    req.write('<div id="ivle_padding">\n')
    req.write("<h2>IVLE Subject Homepages</h2>\n")
    req.write("<h2>Subjects</h2>\n<ul>\n")
    for subject in subjects:
        req.write('  <li><a href="%s">%s</a></li>\n'
            % (urllib.quote(subject) + '/', cgi.escape(subject)))
    req.write("</ul>\n")
    req.write("</div>\n")

def handle_subject_page(req, path):
    req.content_type = "text/html"
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Just make the iframe pointing to media/subjects
    serve_loc = util.make_path(os.path.join('media', 'subjects', path))
    req.write('<iframe src="%s"></iframe>'
        % urllib.quote(serve_loc))
