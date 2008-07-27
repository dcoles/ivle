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
import common.db

def handle(req):
    """Handler for the Subjects application. Links to subject home pages."""

    req.styles = ["media/subjects/subjects.css"]
    if req.path == "":
        handle_toplevel_menu(req)
    else:
        handle_subject_page(req, req.path)

def handle_toplevel_menu(req):
    # This is represented as a directory. Redirect and add a slash if it is
    # missing.
    if req.uri[-1] != '/':
        req.throw_redirect(req.uri + '/')

    # Get list of subjects
    db = common.db.DB()
    try:
        enrolled_subjects = db.get_enrolment(req.user.login)
        all_subjects = db.get_subjects()
    finally:
        db.close()

    enrolled_set = set(x['subj_code'] for x in enrolled_subjects)
    unenrolled_subjects = [x for x in all_subjects
                           if x['subj_code'] not in enrolled_set]
    enrolled_subjects.sort(key=lambda x: x['subj_code'])
    unenrolled_subjects.sort(key=lambda x: x['subj_code'])

    def print_subject(subject):
        if subject['url'] is None:
            req.write('  <li>%s (no home page)</li>\n'
                % cgi.escape(subject['subj_name']))
        else:
            req.write('  <li><a href="%s">%s</a></li>\n'
                % (cgi.escape(subject['url']),
                   cgi.escape(subject['subj_name'])))

    req.content_type = "text/html"
    req.write_html_head_foot = True
    req.write('<div id="ivle_padding">\n')
    req.write("<h2>IVLE Subject Homepages</h2>\n")
    req.write("<h2>Subjects</h2>\n<ul>\n")
    for subject in enrolled_subjects:
        print_subject(subject)
    req.write("</ul>\n")
    if len(unenrolled_subjects) > 0:
        req.write("<h3>Other Subjects</h3>\n")
        req.write("<p>You are not currently enrolled in these subjects</p>\n")
        req.write("<ul>\n")
        for subject in unenrolled_subjects:
            print_subject(subject)
        req.write("</ul>\n")
    req.write("</div>\n")

def handle_subject_page(req, path):
    req.content_type = "text/html"
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Just make the iframe pointing to media/subjects
    serve_loc = util.make_path(os.path.join('media', 'subjects', path))
    req.write('<object class="fullscreen" type="text/html" \
data="%s"></iframe>'% urllib.quote(serve_loc))
