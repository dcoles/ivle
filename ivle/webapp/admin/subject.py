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
import formencode.validators

from ivle.webapp.base.forms import BaseFormView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.base.xhtml import XHTMLView
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
from ivle.webapp.core import Plugin as CorePlugin
from ivle.webapp.groups import GroupsView
from ivle.webapp.media import media_url
from ivle.webapp.tutorial import Plugin as TutorialPlugin

class SubjectsView(XHTMLView):
    '''The view of the list of subjects.'''
    template = 'templates/subjects.html'
    tab = 'subjects'

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        ctx['req'] = req
        ctx['user'] = req.user
        ctx['semesters'] = []
        ctx['mediapath'] = media_url(req, CorePlugin, 'images/')
        ctx['SubjectEdit'] = SubjectEdit

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

        # Admins get a separate list of subjects so they can add/edit.
        if req.user.admin:
            ctx['subjects'] = req.store.find(Subject).order_by(Subject.name)


class SubjectShortNameUniquenessValidator(formencode.FancyValidator):
    """A FormEncode validator that checks that a subject name is unused.

    The subject referenced by state.existing_subject is permitted
    to hold that name. If any other object holds it, the input is rejected.
    """
    def __init__(self, matching=None):
        self.matching = matching

    def _to_python(self, value, state):
        if (state.store.find(
                Subject, short_name=value).one() not in
                (None, state.existing_subject)):
            raise formencode.Invalid(
                'Short name already taken', value, state)
        return value


class SubjectSchema(formencode.Schema):
    short_name = formencode.All(
        SubjectShortNameUniquenessValidator(),
        formencode.validators.UnicodeString(not_empty=True))
    name = formencode.validators.UnicodeString(not_empty=True)
    code = formencode.validators.UnicodeString(not_empty=True)


class SubjectFormView(BaseFormView):
    """An abstract form to add or edit a subject."""
    tab = 'subjects'

    def authorize(self, req):
        return req.user is not None and req.user.admin

    def populate_state(self, state):
        state.existing_subject = None

    @property
    def validator(self):
        return SubjectSchema()

    def get_return_url(self, obj):
        return '/subjects'


class SubjectNew(SubjectFormView):
    """A form to create a subject."""
    template = 'templates/subject-new.html'

    def get_default_data(self, req):
        return {}

    def save_object(self, req, data):
        new_subject = Subject()
        new_subject.short_name = data['short_name']
        new_subject.name = data['name']
        new_subject.code = data['code']

        req.store.add(new_subject)
        return new_subject


class SubjectEdit(SubjectFormView):
    """A form to edit a subject."""
    template = 'templates/subject-edit.html'

    def populate_state(self, state):
        state.existing_subject = self.context

    def get_default_data(self, req):
        return {
            'short_name': self.context.short_name,
            'name': self.context.name,
            'code': self.context.code,
            }

    def save_object(self, req, data):
        self.context.short_name = data['short_name']
        self.context.name = data['name']
        self.context.code = data['code']

        return self.context


class SemesterUniquenessValidator(formencode.FancyValidator):
    """A FormEncode validator that checks that a semester is unique.

    There cannot be more than one semester for the same year and semester.
    """
    def _to_python(self, value, state):
        if (state.store.find(
                Semester, year=value['year'], semester=value['semester']
                ).count() > 0):
            raise formencode.Invalid(
                'Semester already exists', value, state)
        return value


class SemesterSchema(formencode.Schema):
    year = formencode.validators.UnicodeString()
    semester = formencode.validators.UnicodeString()
    chained_validators = [SemesterUniquenessValidator()]


class SemesterNew(BaseFormView):
    """A form to create a semester."""
    template = 'templates/semester-new.html'
    tab = 'subjects'

    def authorize(self, req):
        return req.user is not None and req.user.admin

    @property
    def validator(self):
        return SemesterSchema()

    def get_default_data(self, req):
        return {}

    def save_object(self, req, data):
        new_semester = Semester()
        new_semester.year = data['year']
        new_semester.semester = data['semester']

        req.store.add(new_semester)
        return new_semester

    def get_return_url(self, obj):
        return '/subjects'


class OfferingView(XHTMLView):
    """The home page of an offering."""
    template = 'templates/offering.html'
    tab = 'subjects'
    permission = 'view'

    def populate(self, req, ctx):
        # Need the worksheet result styles.
        self.plugin_styles[TutorialPlugin] = ['tutorial.css']
        ctx['context'] = self.context
        ctx['req'] = req
        ctx['permissions'] = self.context.get_permissions(req.user,req.config)
        ctx['format_submission_principal'] = util.format_submission_principal
        ctx['format_datetime'] = ivle.date.make_date_nice
        ctx['format_datetime_short'] = ivle.date.format_datetime_for_paragraph
        ctx['OfferingEdit'] = OfferingEdit
        ctx['GroupsView'] = GroupsView

        # As we go, calculate the total score for this subject
        # (Assessable worksheets only, mandatory problems only)

        ctx['worksheets'], problems_total, problems_done = (
            ivle.worksheet.utils.create_list_of_fake_worksheets_and_stats(
                req.store, req.user, self.context))

        ctx['exercises_total'] = problems_total
        ctx['exercises_done'] = problems_done
        if problems_total > 0:
            if problems_done >= problems_total:
                ctx['worksheets_complete_class'] = "complete"
            elif problems_done > 0:
                ctx['worksheets_complete_class'] = "semicomplete"
            else:
                ctx['worksheets_complete_class'] = "incomplete"
            # Calculate the final percentage and mark for the subject
            (ctx['exercises_pct'], ctx['worksheet_mark'],
             ctx['worksheet_max_mark']) = (
                ivle.worksheet.utils.calculate_mark(
                    problems_done, problems_total))


class SubjectValidator(formencode.FancyValidator):
    """A FormEncode validator that turns a subject name into a subject.

    The state must have a 'store' attribute, which is the Storm store
    to use.
    """
    def _to_python(self, value, state):
        subject = state.store.find(Subject, short_name=value).one()
        if subject:
            return subject
        else:
            raise formencode.Invalid('Subject does not exist', value, state)


class SemesterValidator(formencode.FancyValidator):
    """A FormEncode validator that turns a string into a semester.

    The string should be of the form 'year/semester', eg. '2009/1'.

    The state must have a 'store' attribute, which is the Storm store
    to use.
    """
    def _to_python(self, value, state):
        try:
            year, semester = value.split('/')
        except ValueError:
            year = semester = None

        semester = state.store.find(
            Semester, year=year, semester=semester).one()
        if semester:
            return semester
        else:
            raise formencode.Invalid('Semester does not exist', value, state)


class OfferingUniquenessValidator(formencode.FancyValidator):
    """A FormEncode validator that checks that an offering is unique.

    There cannot be more than one offering in the same year and semester.

    The offering referenced by state.existing_offering is permitted to
    hold that year and semester tuple. If any other object holds it, the
    input is rejected.
    """
    def _to_python(self, value, state):
        if (state.store.find(
                Offering, subject=value['subject'],
                semester=value['semester']).one() not in
                (None, state.existing_offering)):
            raise formencode.Invalid(
                'Offering already exists', value, state)
        return value


class OfferingSchema(formencode.Schema):
    description = formencode.validators.UnicodeString(
        if_missing=None, not_empty=False)
    url = formencode.validators.URL(if_missing=None, not_empty=False)


class OfferingAdminSchema(OfferingSchema):
    subject = formencode.All(
        SubjectValidator(), formencode.validators.UnicodeString())
    semester = formencode.All(
        SemesterValidator(), formencode.validators.UnicodeString())
    chained_validators = [OfferingUniquenessValidator()]


class OfferingEdit(BaseFormView):
    """A form to edit an offering's details."""
    template = 'templates/offering-edit.html'
    tab = 'subjects'
    permission = 'edit'

    @property
    def validator(self):
        if self.req.user.admin:
            return OfferingAdminSchema()
        else:
            return OfferingSchema()

    def populate(self, req, ctx):
        super(OfferingEdit, self).populate(req, ctx)
        ctx['subjects'] = req.store.find(Subject)
        ctx['semesters'] = req.store.find(Semester)

    def populate_state(self, state):
        state.existing_offering = self.context

    def get_default_data(self, req):
        return {
            'subject': self.context.subject.short_name,
            'semester': self.context.semester.year + '/' +
                        self.context.semester.semester,
            'url': self.context.url,
            'description': self.context.description,
            }

    def save_object(self, req, data):
        if req.user.admin:
            self.context.subject = data['subject']
            self.context.semester = data['semester']
        self.context.description = data['description']
        self.context.url = unicode(data['url']) if data['url'] else None
        return self.context


class OfferingNew(BaseFormView):
    """A form to create an offering."""
    template = 'templates/offering-new.html'
    tab = 'subjects'

    def authorize(self, req):
        return req.user is not None and req.user.admin

    @property
    def validator(self):
        return OfferingAdminSchema()

    def populate(self, req, ctx):
        super(OfferingNew, self).populate(req, ctx)
        ctx['subjects'] = req.store.find(Subject)
        ctx['semesters'] = req.store.find(Semester)

    def populate_state(self, state):
        state.existing_offering = None

    def get_default_data(self, req):
        return {}

    def save_object(self, req, data):
        new_offering = Offering()
        new_offering.subject = data['subject']
        new_offering.semester = data['semester']
        new_offering.description = data['description']
        new_offering.url = unicode(data['url']) if data['url'] else None

        req.store.add(new_offering)
        return new_offering


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
        if (("enrol_" + value) not in
                state.offering.get_permissions(state.user, state.config)):
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
    tab = 'subjects'
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
        ctx['roles_auth'] = self.context.get_permissions(req.user, req.config)
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
    permission = "view_project_submissions"
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
             (ApplicationRoot, ('subjects', '+new'), SubjectNew),
             (ApplicationRoot, ('subjects', '+new-offering'), OfferingNew),
             (ApplicationRoot, ('subjects', '+new-semester'), SemesterNew),
             (Subject, '+edit', SubjectEdit),
             (Offering, '+index', OfferingView),
             (Offering, '+edit', OfferingEdit),
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
