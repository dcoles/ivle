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

from ivle import database
from ivle.database import (User, ProjectGroup, Offering, Subject, Semester,
                           ProjectSet, Project, Enrolment)
from ivle.webapp.errors import NotFound, BadRequest
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin
from ivle.webapp import ApplicationRoot

import ivle.date
import ivle.chat
from ivle import util

class SubmitView(XHTMLView):
    """A view to submit a Subversion repository path for a project."""
    template = 'submit.html'
    tab = 'files'
    permission = 'submit_project'
    subpath_allowed = True

    def __init__(self, req, context, subpath):
        super(SubmitView, self).__init__(req, context, subpath)

        if len(subpath) < 1:
            raise NotFound()
        name = subpath[0]
        # We need to work out which entity owns the repository, so we look
        # at the first two path segments. The first tells us the type.
        self.context = self.get_repository_owner(req.store, name)

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
                raise BadRequest('Path is not permissible for this offering.')

            if project is None:
                raise BadRequest('Specified project does not exist.')

            try:
                ctx['submission'] = project.submit(self.context,
                                    unicode(self.path), revision, req.user)
            except (database.DeadlinePassed, database.SubmissionError), e:
                raise BadRequest(str(e) + ".")

            # The Subversion configuration needs to be updated, to grant
            # tutors and lecturers access to this submission. We have to 
            # commit early so usrmgt-server can see the new submission.
            req.store.commit()

            # Instruct usrmgt-server to rebuild the SVN group authz file.
            msg = {'rebuild_svn_group_config': {}}
            usrmgt = ivle.chat.chat(req.config['usrmgt']['host'],
                                    req.config['usrmgt']['port'],
                                    msg,
                                    req.config['usrmgt']['magic'],
                                    )

            if usrmgt.get('response') in (None, 'failure'):
                raise Exception("Failure creating repository: " + str(usrmgt))

            # Instruct usrmgt-server to rebuild the SVN user authz file.
            msg = {'rebuild_svn_config': {}}
            usrmgt = ivle.chat.chat(req.config['usrmgt']['host'],
                                    req.config['usrmgt']['port'],
                                    msg,
                                    req.config['usrmgt']['magic'],
                                    )

            if usrmgt.get('response') in (None, 'failure'):
                raise Exception("Failure creating repository: " + str(usrmgt))

            self.template = 'submitted.html'
            ctx['project'] = project

        ctx['req'] = req
        ctx['principal'] = self.context
        ctx['offering'] = self.offering
        ctx['path'] = self.path
        ctx['now'] = datetime.datetime.now()
        ctx['format_submission_principal'] = util.format_submission_principal
        ctx['format_datetime'] = ivle.date.make_date_nice
        ctx['format_datetime_short'] = ivle.date.format_datetime_for_paragraph
    
    @property
    def path(self):
        return os.path.join('/', *self.subpath[1:]) if self.subpath else '/'


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
            Subject.short_name == self.path.split('/')[1],
            ).one()

    @property
    def fullpath(self):
        """Get the original path of this request, after the +submit."""
        return os.path.join('/users/', *self.subpath)

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

    @property
    def fullpath(self):
        """Get the original path of this request, after the +submit."""
        return os.path.join('/groups/', *self.subpath)


class Plugin(ViewPlugin):
    views = [(ApplicationRoot, ('+submit', 'users'), UserSubmitView),
             (ApplicationRoot, ('+submit', 'groups'), GroupSubmitView)]

    help = {'Submitting a project': 'help.html'}
