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

import ivle.database
from ivle import util

import genshi
import genshi.template

def handle(req):
    """Handler for the Subjects application. Links to subject home pages."""

    req.styles = ["media/subjects/subjects.css"]
    ctx = genshi.template.Context()
    if req.path == "":
        # This is represented as a directory. Redirect and add a slash if it is
        # missing.
        if req.uri[-1] != '/':
            req.throw_redirect(req.uri + '/')
        ctx['whichpage'] = "toplevel"
        handle_toplevel_menu(req, ctx)
    else:
        ctx['whichpage'] = "subject"
        handle_subject_page(req, req.path, ctx)
        
    loader = genshi.template.TemplateLoader(".", auto_reload=True)
    tmpl = loader.load(util.make_local_path("apps/subjects/template.html"))
    req.write(tmpl.generate(ctx).render('html')) #'xhtml', doctype='xhtml'))

def handle_toplevel_menu(req, ctx):

    enrolled_subjects = req.user.subjects
    unenrolled_subjects = [subject for subject in
                           req.store.find(ivle.database.Subject)
                           if subject not in enrolled_subjects]

    ctx['enrolled_subjects'] = []
    ctx['other_subjects'] = []

    req.content_type = "text/html"
    req.write_html_head_foot = True

    for subject in enrolled_subjects:
        new_subj = {}
        new_subj['name'] = subject.name
        new_subj['url'] = subject.url
        ctx['enrolled_subjects'].append(new_subj)

    if len(unenrolled_subjects) > 0:
        for subject in unenrolled_subjects:
            new_subj = {}
            new_subj['name'] = subject.name
            new_subj['url'] = subject.url
            ctx['other_subjects'].append(new_subj)


def handle_subject_page(req, path, ctx):
    req.content_type = "text/html"
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Just make the iframe pointing to media/subjects
    ctx['serve_loc'] = urllib.quote(util.make_path(os.path.join('media', 'subjects', path)))
