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


class UsersBreadcrumb(object):
    @property
    def url(self):
        return '/users'

    @property
    def text(self):
        return 'Users'


class UserBreadcrumb(object):
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def url(self):
        return self.req.publisher.generate(self.context)

    @property
    def text(self):
        perms = self.context.get_permissions(self.req.user, self.req.config)
        # Show nickname iff current user has permission to view this user
        # (Else, show just the login name)
        if 'view' in perms:
            return self.context.nick
        else:
            return self.context.login

    @property
    def extra_breadcrumbs_before(self):
        return [UsersBreadcrumb()]


class SubjectsBreadcrumb(object):
    @property
    def url(self):
        return '/subjects'

    @property
    def text(self):
        return 'Subjects'

class SubjectBreadcrumb(object):
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def url(self):
        return self.req.publisher.generate(self.context)

    @property
    def text(self):
        return self.context.name

    @property
    def extra_breadcrumbs_before(self):
        return [SubjectsBreadcrumb()]


class OfferingBreadcrumb(object):
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def url(self):
        return self.req.publisher.generate(self.context)

    @property
    def text(self):
        return '%s %s' % (self.context.semester.year,
                          self.context.semester.display_name)


class ProjectsBreadcrumb(object):
    """Static 'Projects' breadcrumb to precede ProjectBreadcrumb.
    context must be a ProjectSet.
    """
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def url(self):
        return self.req.publisher.generate(self.context.offering, None,
                                           '+projects')

    @property
    def text(self):
        return 'Projects'


class ProjectBreadcrumb(object):
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def url(self):
        return self.req.publisher.generate(self.context)

    @property
    def text(self):
        return self.context.name

    @property
    def extra_breadcrumbs_before(self):
        return [ProjectsBreadcrumb(self.req, self.context.project_set)]


class EnrolmentsBreadcrumb(object):
    """Static 'Enrolments' breadcrumb to precede EnrolmentBreadcrumb."""
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def url(self):
        return self.req.publisher.generate(self.context, None, '+enrolments')

    @property
    def text(self):
        return 'Enrolments'


class EnrolmentBreadcrumb(object):
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def text(self):
        return self.context.user.fullname

    @property
    def extra_breadcrumbs_before(self):
        return [EnrolmentsBreadcrumb(self.req, self.context.offering)]
