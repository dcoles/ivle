# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
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

"""Utility functions for filesystem views."""

from ivle.webapp.publisher import ROOT

class FileBreadcrumb(object):
    def __init__(self, req, pathsegments, revno=None, final=False,suffix=None):
        self.req = req
        self.pathsegments = pathsegments
        self.revno = revno
        self.final = final
        self.suffix = suffix

    @property
    def url(self):
        url = self.req.publisher.generate(ROOT, None, ('files',) +
                                       self.pathsegments)
        if self.revno is not None:
            url += '?r=%d' % self.revno
        return url

    @property
    def text(self):
        text = self.pathsegments[-1]
        if self.final and self.revno is not None:
            text += (' (revision %d)' % self.revno)
        if self.suffix:
            text += ' ' + self.suffix
        return text

def make_path_breadcrumbs(req, pathsegments, revno=None, suffix=None):
    """Return breadcrumbs for the segments of the given path."""

    crumbs = []
    for i in range(1, len(pathsegments)):
        crumbs.append(FileBreadcrumb(req, pathsegments[:i], revno))
    crumbs.append(FileBreadcrumb(req, pathsegments, revno, True, suffix))
    return crumbs
