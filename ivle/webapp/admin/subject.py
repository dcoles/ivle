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
import os.path
import urllib
import urlparse
import cgi

from storm.locals import Desc, Store
import genshi
from genshi.filters import HTMLFormFiller
from genshi.template import Context, TemplateLoader
import formencode

from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp import ApplicationRoot

from ivle.database import Subject, Semester, Offering, Enrolment, User,\
                          ProjectSet, Project, ProjectSubmission
from ivle import util
import ivle.date

from ivle.webapp.admin.projectservice import ProjectSetRESTView
from ivle.webapp.admin.offeringservice import OfferingRESTView
from ivle.webapp.admin.publishing import (root_to_subject,
            subject_to_offering, offering_to_projectset, offering_to_project,
            subject_url, offering_url, projectset_url, project_url)
from ivle.webapp.admin.breadcrumbs import (SubjectBreadcrumb,
            OfferingBreadcrumb, UserBreadcrumb, ProjectBreadcrumb)
from ivle.webapp.groups import GroupsView

class SubjectsView(XHTMLView):
    '''The view of the list of subjects.'''
    template = 'templates/subjects.html'
    tab = 'subjects'

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        ctx['user'] = req.user
        ctx['semesters'] = []
        for semester in req.store.find(Semester).order_by(Desc(Semester.year),
                                                     Desc(Semester.semester)):
            if req.user.admin:
                # For admins, show all subjects in the system
                offerings = list(semester.offerings.find())
            else:
                offerings = [enrolment.offering for enrolment in
                                    semester.enrolments.find(user=req.user)]
            if len(offerings):
                ctx['semesters'].append((semester, offerings))


class OfferingView(XHTMLView):
    """The home page of an offering."""
    template = 'templates/offering.html'
    tab = 'subjects'
    permission = 'view'

    def populate(self, req, ctx):
        ctx['context'] = self.context
        ctx['req'] = req
        ctx['permissions'] = self.context.get_permissions(req.user)
        ctx['format_datetime'] = ivle.date.make_date_nice
        ctx['format_datetime_short'] = ivle.date.format_datetime_for_paragraph


class UserValidator(formencode.FancyValidator):
    """A FormEncode validator that turns a username into a user.

    The state must have a 'store' attribute, which is the Storm store
    to use."""
    def _to_python(self, value, state):
        user = User.get_by_login(state.store, value)
        if user:
            return user
        else:
            raise formencode.Invalid('User does not exist', value, state)


class NoEnrolmentValidator(formencode.FancyValidator):
    """A FormEncode validator that ensures absence of an enrolment.

    The state must have an 'offering' attribute.
    """
    def _to_python(self, value, state):
        if state.offering.get_enrolment(value):
            raise formencode.Invalid('User already enrolled', value, state)
        return value


class RoleEnrolmentValidator(formencode.FancyValidator):
    """A FormEncode validator that checks permission to enrol users with a
    particular role.

    The state must have an 'offering' attribute.
    """
    def _to_python(self, value, state):
        if ("enrol_" + value) not in state.offering.get_permissions(state.user):
            raise formencode.Invalid('Not allowed to assign users that role',
                                     value, state)
        return value


class EnrolSchema(formencode.Schema):
    user = formencode.All(NoEnrolmentValidator(), UserValidator())
    role = formencode.All(formencode.validators.OneOf(
                                ["lecturer", "tutor", "student"]),
                          RoleEnrolmentValidator(),
                          formencode.validators.UnicodeString())


class EnrolmentsView(XHTMLView):
    """A page which displays all users enrolled in an offering."""
    template = 'templates/enrolments.html'
    permission = 'edit'

    def populate(self, req, ctx):
        ctx['offering'] = self.context

class EnrolView(XHTMLView):
    """A form to enrol a user in an offering."""
    template = 'templates/enrol.html'
    tab = 'subjects'
    permission = 'enrol'

    def filter(self, stream, ctx):
        return stream | HTMLFormFiller(data=ctx['data'])

    def populate(self, req, ctx):
        if req.method == 'POST':
            data = dict(req.get_fieldstorage())
            try:
                validator = EnrolSchema()
                req.offering = self.context # XXX: Getting into state.
                data = validator.to_python(data, state=req)
                self.context.enrol(data['user'], data['role'])
                req.store.commit()
                req.throw_redirect(req.uri)
            except formencode.Invalid, e:
                errors = e.unpack_errors()
        else:
            data = {}
            errors = {}

        ctx['data'] = data or {}
        ctx['offering'] = self.context
        ctx['roles_auth'] = self.context.get_permissions(req.user)
        ctx['errors'] = errors

class OfferingProjectsView(XHTMLView):
    """View the projects for an offering."""
    template = 'templates/offering_projects.html'
    permission = 'edit'
    tab = 'subjects'

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ["project.css"]
        self.plugin_scripts[Plugin] = ["project.js"]
        ctx['req'] = req
        ctx['offering'] = self.context
        ctx['projectsets'] = []
        ctx['OfferingRESTView'] = OfferingRESTView

        #Open the projectset Fragment, and render it for inclusion
        #into the ProjectSets page
        #XXX: This could be a lot cleaner
        loader = genshi.template.TemplateLoader(".", auto_reload=True)

        set_fragment = os.path.join(os.path.dirname(__file__),
                "templates/projectset_fragment.html")
        project_fragment = os.path.join(os.path.dirname(__file__),
                "templates/project_fragment.html")

        for projectset in self.context.project_sets:
            settmpl = loader.load(set_fragment)
            setCtx = Context()
            setCtx['req'] = req
            setCtx['projectset'] = projectset
            setCtx['projects'] = []
            setCtx['GroupsView'] = GroupsView
            setCtx['ProjectSetRESTView'] = ProjectSetRESTView

            for project in projectset.projects:
                projecttmpl = loader.load(project_fragment)
                projectCtx = Context()
                projectCtx['req'] = req
                projectCtx['project'] = project

                setCtx['projects'].append(
                        projecttmpl.generate(projectCtx))

            ctx['projectsets'].append(settmpl.generate(setCtx))


class ProjectView(XHTMLView):
    """View the submissions for a ProjectSet"""
    template = "templates/project.html"
    permission = "edit"
    tab = 'subjects'

    def build_subversion_url(self, svnroot, submission):
        princ = submission.assessed.principal

        if isinstance(princ, User):
            path = 'users/%s' % princ.login
        else:
            path = 'groups/%s_%s_%s_%s' % (
                    princ.project_set.offering.subject.short_name,
                    princ.project_set.offering.semester.year,
                    princ.project_set.offering.semester.semester,
                    princ.name
                    )
        return urlparse.urljoin(
                    svnroot,
                    os.path.join(path, submission.path[1:] if
                                       submission.path.startswith(os.sep) else
                                       submission.path))

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ["project.css"]

        ctx['req'] = req
        ctx['GroupsView'] = GroupsView
        ctx['EnrolView'] = EnrolView
        ctx['format_datetime_short'] = ivle.date.format_datetime_for_paragraph
        ctx['build_subversion_url'] = self.build_subversion_url
        ctx['svn_addr'] = req.config['urls']['svn_addr']
        ctx['project'] = self.context
        ctx['user'] = req.user

class Plugin(ViewPlugin, MediaPlugin):
    forward_routes = (root_to_subject, subject_to_offering,
                      offering_to_project, offering_to_projectset)
    reverse_routes = (subject_url, offering_url, projectset_url, project_url)

    views = [(ApplicationRoot, ('subjects', '+index'), SubjectsView),
             (Offering, '+index', OfferingView),
             (Offering, ('+enrolments', '+index'), EnrolmentsView),
             (Offering, ('+enrolments', '+new'), EnrolView),
             (Offering, ('+projects', '+index'), OfferingProjectsView),
             (Project, '+index', ProjectView),

             (Offering, ('+projectsets', '+new'), OfferingRESTView, 'api'),
             (ProjectSet, ('+projects', '+new'), ProjectSetRESTView, 'api'),
             ]

    breadcrumbs = {Subject: SubjectBreadcrumb,
                   Offering: OfferingBreadcrumb,
                   User: UserBreadcrumb,
                   Project: ProjectBreadcrumb,
                   }

    tabs = [
        ('subjects', 'Subjects',
         'View subject content and complete worksheets',
         'subjects.png', 'subjects', 5)
    ]

    media = 'subject-media'
