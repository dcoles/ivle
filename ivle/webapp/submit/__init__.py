# IVLE
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

# Author: Will Grant

"""Project submissions user interface."""

import os.path
import datetime

from storm.locals import Store

from ivle.database import (User, ProjectGroup, Offering, Subject, Semester,
                           ProjectSet, Project, Enrolment)
from ivle.webapp.errors import NotFound, BadRequest
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin

import ivle.date


class SubmitView(XHTMLView):
    """A view to submit a Subversion repository path for a project."""
    template = 'submit.html'
    tab = 'files'
    permission = 'submit_project'

    def __init__(self, req, name, path):
        # We need to work out which entity owns the repository, so we look
        # at the first two path segments. The first tells us the type.
        self.context = self.get_repository_owner(req.store, name)
        self.path = os.path.normpath(path)

        if self.context is None:
            raise NotFound()

        self.offering = self.get_offering()

    def get_repository_owner(self, store, name):
        """Return the owner of the repository given the name and a Store."""
        raise NotImplementedError()

    def get_offering(self):
        """Return the offering that this path can be submitted to."""
        raise NotImplementedError()

    def populate(self, req, ctx):
        if req.method == 'POST':
            data = dict(req.get_fieldstorage())
            if 'revision' not in data:
                raise BadRequest('No revision selected.')

            try:
                revision = int(data['revision'])
            except ValueError:
                raise BadRequest('Revision must be an integer.')

            if 'project' not in data:
                raise BadRequest('No project selected.')

            try:
                projectid = int(data['project'])
            except ValueError:
                raise BadRequest('Project must be an integer.')

            project = req.store.find(Project, Project.id == projectid).one()

            # This view's offering will be the sole offering for which the
            # path is permissible. We need to check that.
            if project.project_set.offering is not self.offering:
                raise BadRequest('Path is not permissible for this offering')

            if project is None:
                raise BadRequest('Specified project does not exist')

            project.submit(self.context, self.path, revision, req.user)

            self.template = 'submitted.html'
            ctx['project'] = project

        ctx['req'] = req
        ctx['principal'] = self.context
        ctx['offering'] = self.offering
        ctx['path'] = self.path
        ctx['now'] = datetime.datetime.now()
        ctx['format_datetime'] = ivle.date.format_datetime_for_paragraph


class UserSubmitView(SubmitView):
    def get_repository_owner(self, store, name):
        '''Resolve the user name into a user.'''
        return User.get_by_login(store, name)

    def get_offering(self):
        return Store.of(self.context).find(Offering,
            Offering.id == Enrolment.offering_id,
            Enrolment.user_id == self.context.id,
            Offering.semester_id == Semester.id,
            Semester.state == u'current',
            Offering.subject_id == Subject.id,
            Subject.short_name == self.path.split('/')[0],
            ).one()


class GroupSubmitView(SubmitView):
    def get_repository_owner(self, store, name):
        '''Resolve the subject_year_semester_group name into a group.'''
        namebits = name.split('_', 3)
        if len(namebits) != 4:
            return None

        # Find the project group with the given name in any project set in the
        # offering of the given subject in the semester with the given year
        # and semester.
        return store.find(ProjectGroup,
            ProjectGroup.name == namebits[3],
            ProjectGroup.project_set_id == ProjectSet.id,
            ProjectSet.offering_id == Offering.id,
            Offering.subject_id == Subject.id,
            Subject.short_name == namebits[0],
            Offering.semester_id == Semester.id,
            Semester.year == namebits[1],
            Semester.semester == namebits[2]).one()

    def get_offering(self):
        return self.context.project_set.offering


class Plugin(ViewPlugin):
    urls = [
        ('+submit/users/:name/*path', UserSubmitView),
        ('+submit/groups/:name/*path', GroupSubmitView),
    ]
