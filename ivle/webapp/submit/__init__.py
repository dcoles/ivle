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

from ivle.database import (User, ProjectGroup, Offering, Subject, Semester,
                           ProjectSet)
from ivle.webapp.errors import NotFound
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin


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

    def get_repository_owner(self, store, name):
        """Return the owner of the repository given the name and a Store."""
        raise NotImplementedError()

    def populate(self, req, ctx):
        ctx['principal'] = self.context
        ctx['path'] = self.path


class UserSubmitView(SubmitView):
    def get_repository_owner(self, store, name):
        '''Resolve the user name into a user.'''
        return User.get_by_login(store, name)


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


class Plugin(ViewPlugin):
    urls = [
        ('+submit/users/:name/*path', UserSubmitView),
        ('+submit/groups/:name/*path', GroupSubmitView),
    ]
