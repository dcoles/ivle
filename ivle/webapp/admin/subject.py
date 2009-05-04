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

from storm.locals import Desc
import genshi
from genshi.filters import HTMLFormFiller
from genshi.template import Context, TemplateLoader
import formencode

from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.errors import NotFound

from ivle.database import Subject, Semester, Offering, Enrolment, User,\
                          ProjectSet, Project, ProjectSubmission
from ivle import util

from ivle.webapp.admin.projectservice import ProjectSetRESTView,\
                                             ProjectRESTView
from ivle.webapp.admin.offeringservice import OfferingRESTView


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
            enrolments = semester.enrolments.find(user=req.user)
            if enrolments.count():
                ctx['semesters'].append((semester, enrolments))


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


class EnrolSchema(formencode.Schema):
    user = formencode.All(NoEnrolmentValidator(), UserValidator())


class EnrolView(XHTMLView):
    """A form to enrol a user in an offering."""
    template = 'templates/enrol.html'
    tab = 'subjects'
    permission = 'edit'

    def __init__(self, req, subject, year, semester):
        """Find the given offering by subject, year and semester."""
        self.context = req.store.find(Offering,
            Offering.subject_id == Subject.id,
            Subject.short_name == subject,
            Offering.semester_id == Semester.id,
            Semester.year == year,
            Semester.semester == semester).one()

        if not self.context:
            raise NotFound()

    def filter(self, stream, ctx):
        return stream | HTMLFormFiller(data=ctx['data'])

    def populate(self, req, ctx):
        if req.method == 'POST':
            data = dict(req.get_fieldstorage())
            try:
                validator = EnrolSchema()
                req.offering = self.context # XXX: Getting into state.
                data = validator.to_python(data, state=req)
                self.context.enrol(data['user'])
                req.store.commit()
                req.throw_redirect(req.uri)
            except formencode.Invalid, e:
                errors = e.unpack_errors()
        else:
            data = {}
            errors = {}

        ctx['data'] = data or {}
        ctx['offering'] = self.context
        ctx['errors'] = errors

class SubjectProjectSetView(XHTMLView):
    """View the ProjectSets for a subject."""
    template = 'templates/subject_projects.html'
    permission = 'edit'
    
    def __init__(self, req, subject, year, semester):
        self.context = req.store.find(Offering,
            Offering.subject_id == Subject.id,
            Subject.short_name == subject,
            Offering.semester_id == Semester.id,
            Semester.year == year,
            Semester.semester == semester).one()

        if not self.context:
            raise NotFound()

    def project_url(self, projectset, project):
        return "/subjects/" + self.context.subject.short_name + "/" +\
                self.context.semester.year + "/" + \
                self.context.semester.semester + "/+projectsets/" +\
                str(projectset.id) + "/+projects/" + project.short_name

    def new_project_url(self, projectset):
        return "/api/subjects/" + self.context.subject.short_name + "/" +\
                self.context.semester.year + "/" + \
                self.context.semester.semester + "/+projectsets/" +\
                str(projectset.id) + "/+projects/+new"
    
    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ["project.css"]
        self.plugin_scripts[Plugin] = ["project.js"]
        ctx['offering'] = self.context
        ctx['subject'] = self.context.subject.short_name
        ctx['year'] = self.context.semester.year
        ctx['semester'] = self.context.semester.semester

        ctx['projectsets'] = []

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
            setCtx['group_size'] = projectset.max_students_per_group
            setCtx['projectset_id'] = projectset.id
            setCtx['new_project_url'] = self.new_project_url(projectset)
            setCtx['projects'] = []

            for project in projectset.projects:
                projecttmpl = loader.load(project_fragment)
                projectCtx = Context()
                projectCtx['project'] = project
                projectCtx['project_url'] = self.project_url(projectset, project)

                setCtx['projects'].append(
                        projecttmpl.generate(projectCtx))

            ctx['projectsets'].append(settmpl.generate(setCtx))


class ProjectView(XHTMLView):
    """View the submissions for a ProjectSet"""
    template = "templates/project.html"
    permission = "edit"

    def __init__(self, req, subject, year, semester, projectset, project):
        self.context = req.store.find(Project,
                Project.short_name == project,
                Project.project_set_id == ProjectSet.id,
                ProjectSet.offering_id == Offering.id,
                Offering.semester_id == Semester.id,
                Semester.year == year,
                Semester.semester == semester,
                Offering.subject_id == Subject.id,
                Subject.short_name == subject).one()
        if self.context is None:
            raise NotFound()

    def populate(self, req, ctx):
        ctx['project'] = self.context
        ctx['assesseds'] = self.context.assesseds

        ctx['submissions'] = []
        for assessed in self.context.assesseds:
            if assessed.submissions.count() > 0:
                ctx['submissions'].append(
                        assessed.submissions.order_by(ProjectSubmission.date_submitted)[-1])


class Plugin(ViewPlugin, MediaPlugin):
    urls = [
        ('subjects/', SubjectsView),
        ('subjects/:subject/:year/:semester/+enrolments/+new', EnrolView),
        ('subjects/:subject/:year/:semester/+projects', SubjectProjectSetView),
        ('subjects/:subject/:year/:semester/+projectsets/:projectset/+projects/:project', ProjectView),
        #API Views
        ('api/subjects/:subject/:year/:semester/+projectsets/+new',
            OfferingRESTView),
        ('api/subjects/:subject/:year/:semester/+projectsets/:projectset/+projects/+new',
            ProjectSetRESTView),
        ('api/subjects/:subject/:year/:semester/+projectsets/:projectset/+projects/:project', 
            ProjectRESTView),

    ]

    tabs = [
        ('subjects', 'Subjects',
         'View subject content and complete worksheets',
         'subjects.png', 'subjects', 5)
    ]

    media = 'subject-media'
