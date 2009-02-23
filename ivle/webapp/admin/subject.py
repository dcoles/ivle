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

from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.errors import NotFound
from ivle.database import Subject
from ivle import util


class SubjectsView(XHTMLView):
    '''The view of the list of subjects.'''
    template = 'subjects.html'
    appname = 'subjects' # XXX

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        enrolled_subjects = req.user.subjects
        unenrolled_subjects = [subject for subject in
                               req.store.find(Subject)
                               if subject not in enrolled_subjects]

        ctx['enrolled_subjects'] = []
        ctx['other_subjects'] = []

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


class Plugin(ViewPlugin, MediaPlugin):
    urls = [
        ('subjects/', SubjectsView),
    ]

    tabs = [
        ('subjects', 'Subjects', 'Announcements and information about the '
         'subjects you are enrolled in.', 'subjects.png', 'subjects', 5)
    ]

    media = 'subject-media'
