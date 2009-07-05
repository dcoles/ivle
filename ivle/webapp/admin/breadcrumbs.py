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

from ivle.database import Offering

class UserBreadcrumb(object):
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def url(self):
        return self.req.router.generate(self.context)

    @property
    def text(self):
        return self.context.nick

class SubjectBreadcrumb(object):
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def text(self):
        return self.context.name

class OfferingBreadcrumb(object):
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def url(self):
        return self.req.router.generate(self.context)

    @property
    def text(self):
        return '%s semester %s' % (self.context.semester.year,
                                   self.context.semester.semester)

    @property
    def menu(self):
        return {
            'Worksheets': self.req.router.generate(self.context, None,
                                                   ('+worksheets')),
            }
