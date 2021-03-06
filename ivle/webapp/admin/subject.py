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
import datetime

from storm.locals import Desc, Store
import genshi
from genshi.filters import HTMLFormFiller
from genshi.template import Context
import formencode
import formencode.validators

from ivle.webapp.base.forms import (BaseFormView, URLNameValidator,
                                    DateTimeValidator)
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.text import TextView
from ivle.webapp.errors import BadRequest
from ivle.webapp import ApplicationRoot

from ivle.database import Subject, Semester, Offering, Enrolment, User,\
                          ProjectSet, Project, ProjectSubmission
from ivle import util
import ivle.date

from ivle.webapp.admin.publishing import (root_to_subject, root_to_semester,
            subject_to_offering, offering_to_projectset, offering_to_project,
            offering_to_enrolment, subject_url, semester_url, offering_url,
            projectset_url, project_url, enrolment_url)
from ivle.webapp.admin.breadcrumbs import (SubjectBreadcrumb,
            OfferingBreadcrumb, UserBreadcrumb, ProjectBreadcrumb,
            ProjectsBreadcrumb, EnrolmentBreadcrumb)
from ivle.webapp.core import Plugin as CorePlugin
from ivle.webapp.groups import GroupsView
from ivle.webapp.media import media_url
from ivle.webapp.tutorial import Plugin as TutorialPlugin

class SubjectsView(XHTMLView):
    '''The view of the list of subjects.'''
    template = 'templates/subjects.html'
    tab = 'subjects'
    breadcrumb_text = "Subjects"

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        ctx['req'] = req
        ctx['user'] = req.user
        ctx['semesters'] = []

        for semester in req.store.find(Semester).order_by(
            Desc(Semester.year), Desc(Semester.display_name)):
            if req.user.admin:
                # For admins, show all subjects in the system
                offerings = list(semester.offerings.find())
            else:
                offerings = [enrolment.offering for enrolment in
                                    semester.enrolments.find(user=req.user)]
            if len(offerings):
                ctx['semesters'].append((semester, offerings))


class SubjectsManage(XHTMLView):
    '''Subject management view.'''
    template = 'templates/subjects-manage.html'
    tab = 'subjects'

    def authorize(self, req):
        return req.user is not None and req.user.admin

    def populate(self, req, ctx):
        ctx['req'] = req
        ctx['mediapath'] = media_url(req, CorePlugin, 'images/')
        ctx['SubjectView'] = SubjectView
        ctx['SubjectEdit'] = SubjectEdit
        ctx['SemesterEdit'] = SemesterEdit

        ctx['subjects'] = req.store.find(Subject).order_by(Subject.name)
        ctx['semesters'] = req.store.find(Semester).order_by(
            Semester.year, Semester.display_name)


class SubjectUniquenessValidator(formencode.FancyValidator):
    """A FormEncode validator that checks that a subject attribute is unique.

    The subject referenced by state.existing_subject is permitted
    to hold that name. If any other object holds it, the input is rejected.

    :param attribute: the name of the attribute to check.
    :param display: a string to identify the field in case of error.
    """

    def __init__(self, attribute, display):
        self.attribute = attribute
        self.display = display

    def _to_python(self, value, state):
        if (state.store.find(Subject, **{self.attribute: value}).one() not in
                (None, state.existing_subject)):
            raise formencode.Invalid(
                '%s already taken' % self.display, value, state)
        return value


class SubjectSchema(formencode.Schema):
    short_name = formencode.All(
        SubjectUniquenessValidator('short_name', 'URL name'),
        URLNameValidator(not_empty=True))
    name = formencode.validators.UnicodeString(not_empty=True)
    code = formencode.All(
        SubjectUniquenessValidator('code', 'Subject code'),
        formencode.validators.UnicodeString(not_empty=True))


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
                Semester, year=value['year'], url_name=value['url_name']
                ).one() not in (None, state.existing_semester)):
            raise formencode.Invalid(
                'Semester already exists', value, state)
        return value


class SemesterSchema(formencode.Schema):
    year = URLNameValidator()
    code = formencode.validators.UnicodeString()
    url_name = URLNameValidator()
    display_name = formencode.validators.UnicodeString()
    state = formencode.All(
        formencode.validators.OneOf(["past", "current", "future"]),
        formencode.validators.UnicodeString())
    chained_validators = [SemesterUniquenessValidator()]


class SemesterFormView(BaseFormView):
    tab = 'subjects'

    def authorize(self, req):
        return req.user is not None and req.user.admin

    @property
    def validator(self):
        return SemesterSchema()

    def get_return_url(self, obj):
        return '/subjects/+manage'


class SemesterNew(SemesterFormView):
    """A form to create a semester."""
    template = 'templates/semester-new.html'
    tab = 'subjects'

    def populate_state(self, state):
        state.existing_semester = None

    def get_default_data(self, req):
        return {}

    def save_object(self, req, data):
        new_semester = Semester()
        new_semester.year = data['year']
        new_semester.code = data['code']
        new_semester.url_name = data['url_name']
        new_semester.display_name = data['display_name']
        new_semester.state = data['state']

        req.store.add(new_semester)
        return new_semester


class SemesterEdit(SemesterFormView):
    """A form to edit a semester."""
    template = 'templates/semester-edit.html'

    def populate_state(self, state):
        state.existing_semester = self.context

    def get_default_data(self, req):
        return {
            'year': self.context.year,
            'code': self.context.code,
            'url_name': self.context.url_name,
            'display_name': self.context.display_name,
            'state': self.context.state,
            }

    def save_object(self, req, data):
        self.context.year = data['year']
        self.context.code = data['code']
        self.context.url_name = data['url_name']
        self.context.display_name = data['display_name']
        self.context.state = data['state']

        return self.context

class SubjectView(XHTMLView):
    '''The view of the list of offerings in a given subject.'''
    template = 'templates/subject.html'
    tab = 'subjects'

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        ctx['context'] = self.context
        ctx['req'] = req
        ctx['user'] = req.user
        ctx['offerings'] = list(self.context.offerings)
        ctx['permissions'] = self.context.get_permissions(req.user,req.config)
        ctx['SubjectEdit'] = SubjectEdit
        ctx['SubjectOfferingNew'] = SubjectOfferingNew


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
        ctx['OfferingCloneWorksheets'] = OfferingCloneWorksheets
        ctx['GroupsView'] = GroupsView
        ctx['EnrolmentsView'] = EnrolmentsView
        ctx['Project'] = ivle.database.Project

        # As we go, calculate the total score for this subject
        # (Assessable worksheets only, mandatory problems only)

        ctx['worksheets'], problems_total, problems_done = (
            ivle.worksheet.utils.create_list_of_fake_worksheets_and_stats(
                req.config, req.store, req.user, self.context,
                as_of=self.context.worksheet_cutoff))

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
            Semester, year=year, url_name=semester).one()
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
    worksheet_cutoff = DateTimeValidator(if_missing=None, not_empty=False)
    show_worksheet_marks = formencode.validators.StringBoolean(
        if_missing=False)


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
        ctx['subjects'] = req.store.find(Subject).order_by(Subject.name)
        ctx['semesters'] = req.store.find(Semester).order_by(
            Semester.year, Semester.display_name)
        ctx['force_subject'] = None

    def populate_state(self, state):
        state.existing_offering = self.context

    def get_default_data(self, req):
        return {
            'subject': self.context.subject.short_name,
            'semester': self.context.semester.year + '/' +
                        self.context.semester.url_name,
            'url': self.context.url,
            'description': self.context.description,
            'worksheet_cutoff': self.context.worksheet_cutoff,
            'show_worksheet_marks': self.context.show_worksheet_marks,
            }

    def save_object(self, req, data):
        if req.user.admin:
            self.context.subject = data['subject']
            self.context.semester = data['semester']
        self.context.description = data['description']
        self.context.url = unicode(data['url']) if data['url'] else None
        self.context.worksheet_cutoff = data['worksheet_cutoff']
        self.context.show_worksheet_marks = data['show_worksheet_marks']
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
        ctx['subjects'] = req.store.find(Subject).order_by(Subject.name)
        ctx['semesters'] = req.store.find(Semester).order_by(
            Semester.year, Semester.display_name)
        ctx['force_subject'] = None

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
        new_offering.worksheet_cutoff = data['worksheet_cutoff']
        new_offering.show_worksheet_marks = data['show_worksheet_marks']

        req.store.add(new_offering)
        return new_offering

class SubjectOfferingNew(OfferingNew):
    """A form to create an offering for a given subject."""
    # Identical to OfferingNew, except it forces the subject to be the subject
    # in context
    def populate(self, req, ctx):
        super(SubjectOfferingNew, self).populate(req, ctx)
        ctx['force_subject'] = self.context

class OfferingCloneWorksheetsSchema(formencode.Schema):
    subject = formencode.All(
        SubjectValidator(), formencode.validators.UnicodeString())
    semester = formencode.All(
        SemesterValidator(), formencode.validators.UnicodeString())


class OfferingCloneWorksheets(BaseFormView):
    """A form to clone worksheets from one offering to another."""
    template = 'templates/offering-clone-worksheets.html'
    tab = 'subjects'

    def authorize(self, req):
        return req.user is not None and req.user.admin

    @property
    def validator(self):
        return OfferingCloneWorksheetsSchema()

    def populate(self, req, ctx):
        super(OfferingCloneWorksheets, self).populate(req, ctx)
        ctx['subjects'] = req.store.find(Subject).order_by(Subject.name)
        ctx['semesters'] = req.store.find(Semester).order_by(
            Semester.year, Semester.display_name)

    def get_default_data(self, req):
        return {}

    def save_object(self, req, data):
        if self.context.worksheets.count() > 0:
            raise BadRequest(
                "Cannot clone to target with existing worksheets.")
        offering = req.store.find(
            Offering, subject=data['subject'], semester=data['semester']).one()
        if offering is None:
            raise BadRequest("No such offering.")
        if offering.worksheets.count() == 0:
            raise BadRequest("Source offering has no worksheets.")

        self.context.clone_worksheets(offering)
        return self.context


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
    breadcrumb_text = 'Enrolments'

    def populate(self, req, ctx):
        ctx['req'] = req
        ctx['offering'] = self.context
        ctx['mediapath'] = media_url(req, CorePlugin, 'images/')
        ctx['offering_perms'] = self.context.get_permissions(
            req.user, req.config)
        ctx['EnrolView'] = EnrolView
        ctx['EnrolmentEdit'] = EnrolmentEdit
        ctx['EnrolmentDelete'] = EnrolmentDelete


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
        # If all of the fields validated, set the global form error.
        if isinstance(errors, basestring):
            ctx['error_value'] = errors


class EnrolmentEditSchema(formencode.Schema):
    role = formencode.All(formencode.validators.OneOf(
                                ["lecturer", "tutor", "student"]),
                          RoleEnrolmentValidator(),
                          formencode.validators.UnicodeString())


class EnrolmentEdit(BaseFormView):
    """A form to alter an enrolment's role."""
    template = 'templates/enrolment-edit.html'
    tab = 'subjects'
    permission = 'edit'

    def populate_state(self, state):
        state.offering = self.context.offering

    def get_default_data(self, req):
        return {'role': self.context.role}

    @property
    def validator(self):
        return EnrolmentEditSchema()

    def save_object(self, req, data):
        self.context.role = data['role']

    def get_return_url(self, obj):
        return self.req.publisher.generate(
            self.context.offering, EnrolmentsView)

    def populate(self, req, ctx):
        super(EnrolmentEdit, self).populate(req, ctx)
        ctx['offering_perms'] = self.context.offering.get_permissions(
            req.user, req.config)


class EnrolmentDelete(XHTMLView):
    """A form to alter an enrolment's role."""
    template = 'templates/enrolment-delete.html'
    tab = 'subjects'
    permission = 'edit'

    def populate(self, req, ctx):
        # If POSTing, delete delete delete.
        if req.method == 'POST':
            self.context.delete()
            req.store.commit()
            req.throw_redirect(req.publisher.generate(
                self.context.offering, EnrolmentsView))

        ctx['enrolment'] = self.context


class OfferingProjectsView(XHTMLView):
    """View the projects for an offering."""
    template = 'templates/offering_projects.html'
    permission = 'edit'
    tab = 'subjects'
    breadcrumb_text = 'Projects'

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ["project.css"]
        ctx['req'] = req
        ctx['offering'] = self.context
        ctx['projectsets'] = []

        #Open the projectset Fragment, and render it for inclusion
        #into the ProjectSets page
        set_fragment = os.path.join(os.path.dirname(__file__),
                "templates/projectset_fragment.html")
        project_fragment = os.path.join(os.path.dirname(__file__),
                "templates/project_fragment.html")

        for projectset in \
            self.context.project_sets.order_by(ivle.database.ProjectSet.id):
            settmpl = self._loader.load(set_fragment)
            setCtx = Context()
            setCtx['req'] = req
            setCtx['projectset'] = projectset
            setCtx['projects'] = []
            setCtx['GroupsView'] = GroupsView
            setCtx['ProjectSetEdit'] = ProjectSetEdit
            setCtx['ProjectNew'] = ProjectNew

            for project in \
                projectset.projects.order_by(ivle.database.Project.deadline):
                projecttmpl = self._loader.load(project_fragment)
                projectCtx = Context()
                projectCtx['req'] = req
                projectCtx['project'] = project
                projectCtx['ProjectEdit'] = ProjectEdit
                projectCtx['ProjectDelete'] = ProjectDelete

                setCtx['projects'].append(
                        projecttmpl.generate(projectCtx))

            ctx['projectsets'].append(settmpl.generate(setCtx))


class ProjectView(XHTMLView):
    """View the submissions for a ProjectSet"""
    template = "templates/project.html"
    permission = "view_project_submissions"
    tab = 'subjects'

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ["project.css"]

        ctx['req'] = req
        ctx['permissions'] = self.context.get_permissions(req.user,req.config)
        ctx['GroupsView'] = GroupsView
        ctx['EnrolView'] = EnrolView
        ctx['format_datetime'] = ivle.date.make_date_nice
        ctx['format_datetime_short'] = ivle.date.format_datetime_for_paragraph
        ctx['project'] = self.context
        ctx['user'] = req.user
        ctx['ProjectEdit'] = ProjectEdit
        ctx['ProjectDelete'] = ProjectDelete
        ctx['ProjectExport'] = ProjectBashExportView

class ProjectBashExportView(TextView):
    """Produce a Bash script for exporting projects"""
    template = "templates/project-export.sh"
    content_type = "text/x-sh"
    permission = "view_project_submissions"

    def populate(self, req, ctx):
        ctx['req'] = req
        ctx['permissions'] = self.context.get_permissions(req.user,req.config)
        ctx['format_datetime'] = ivle.date.make_date_nice
        ctx['format_datetime_short'] = ivle.date.format_datetime_for_paragraph
        ctx['project'] = self.context
        ctx['user'] = req.user
        ctx['now'] = datetime.datetime.now()
        ctx['format_datetime'] = ivle.date.make_date_nice
        ctx['format_datetime_short'] = ivle.date.format_datetime_for_paragraph

class ProjectUniquenessValidator(formencode.FancyValidator):
    """A FormEncode validator that checks that a project short_name is unique
    in a given offering.

    The project referenced by state.existing_project is permitted to
    hold that short_name. If any other project holds it, the input is rejected.
    """
    def _to_python(self, value, state):
        if (state.store.find(
            Project,
            Project.short_name == unicode(value),
            Project.project_set_id == ProjectSet.id,
            ProjectSet.offering == state.offering).one() not in
            (None, state.existing_project)):
            raise formencode.Invalid(
                "A project with that URL name already exists in this offering."
                , value, state)
        return value

class ProjectSchema(formencode.Schema):
    name = formencode.validators.UnicodeString(not_empty=True)
    short_name = formencode.All(
        URLNameValidator(not_empty=True),
        ProjectUniquenessValidator())
    deadline = DateTimeValidator(not_empty=True)
    url = formencode.validators.URL(if_missing=None, not_empty=False)
    synopsis = formencode.validators.UnicodeString(not_empty=True)

class ProjectEdit(BaseFormView):
    """A form to edit a project."""
    template = 'templates/project-edit.html'
    tab = 'subjects'
    permission = 'edit'

    @property
    def validator(self):
        return ProjectSchema()

    def populate(self, req, ctx):
        super(ProjectEdit, self).populate(req, ctx)
        ctx['projectset'] = self.context.project_set

    def populate_state(self, state):
        state.offering = self.context.project_set.offering
        state.existing_project = self.context

    def get_default_data(self, req):
        return {
            'name':         self.context.name,
            'short_name':   self.context.short_name,
            'deadline':     self.context.deadline,
            'url':          self.context.url,
            'synopsis':     self.context.synopsis,
            }

    def save_object(self, req, data):
        self.context.name = data['name']
        self.context.short_name = data['short_name']
        self.context.deadline = data['deadline']
        self.context.url = unicode(data['url']) if data['url'] else None
        self.context.synopsis = data['synopsis']
        return self.context

class ProjectNew(BaseFormView):
    """A form to create a new project."""
    template = 'templates/project-new.html'
    tab = 'subjects'
    permission = 'edit'

    @property
    def validator(self):
        return ProjectSchema()

    def populate(self, req, ctx):
        super(ProjectNew, self).populate(req, ctx)
        ctx['projectset'] = self.context

    def populate_state(self, state):
        state.offering = self.context.offering
        state.existing_project = None

    def get_default_data(self, req):
        return {}

    def save_object(self, req, data):
        new_project = Project()
        new_project.project_set = self.context
        new_project.name = data['name']
        new_project.short_name = data['short_name']
        new_project.deadline = data['deadline']
        new_project.url = unicode(data['url']) if data['url'] else None
        new_project.synopsis = data['synopsis']
        req.store.add(new_project)
        return new_project

class ProjectDelete(XHTMLView):
    """A form to delete a project."""
    template = 'templates/project-delete.html'
    tab = 'subjects'
    permission = 'edit'

    def populate(self, req, ctx):
        # If post, delete the project, or display a message explaining that
        # the project cannot be deleted
        if self.context.can_delete:
            if req.method == 'POST':
                self.context.delete()
                self.template = 'templates/project-deleted.html'
        else:
            # Can't delete
            self.template = 'templates/project-undeletable.html'

        # If get and can delete, display a delete confirmation page

        # Variables for the template
        ctx['req'] = req
        ctx['project'] = self.context
        ctx['OfferingProjectsView'] = OfferingProjectsView

class ProjectSetSchema(formencode.Schema):
    group_size = formencode.validators.Int(if_missing=None, not_empty=False)

class ProjectSetEdit(BaseFormView):
    """A form to edit a project set."""
    template = 'templates/projectset-edit.html'
    tab = 'subjects'
    permission = 'edit'

    @property
    def validator(self):
        return ProjectSetSchema()

    def populate(self, req, ctx):
        super(ProjectSetEdit, self).populate(req, ctx)

    def get_default_data(self, req):
        return {
            'group_size': self.context.max_students_per_group,
            }

    def save_object(self, req, data):
        self.context.max_students_per_group = data['group_size']
        return self.context

class ProjectSetNew(BaseFormView):
    """A form to create a new project set."""
    template = 'templates/projectset-new.html'
    tab = 'subjects'
    permission = 'edit'
    breadcrumb_text = "Projects"

    @property
    def validator(self):
        return ProjectSetSchema()

    def populate(self, req, ctx):
        super(ProjectSetNew, self).populate(req, ctx)

    def get_default_data(self, req):
        return {}

    def save_object(self, req, data):
        new_set = ProjectSet()
        new_set.offering = self.context
        new_set.max_students_per_group = data['group_size']
        req.store.add(new_set)
        return new_set

class Plugin(ViewPlugin, MediaPlugin):
    forward_routes = (root_to_subject, root_to_semester, subject_to_offering,
                      offering_to_project, offering_to_projectset,
                      offering_to_enrolment)
    reverse_routes = (
        subject_url, semester_url, offering_url, projectset_url, project_url,
        enrolment_url)

    views = [(ApplicationRoot, ('subjects', '+index'), SubjectsView),
             (ApplicationRoot, ('subjects', '+manage'), SubjectsManage),
             (ApplicationRoot, ('subjects', '+new'), SubjectNew),
             (ApplicationRoot, ('subjects', '+new-offering'), OfferingNew),
             (ApplicationRoot, ('+semesters', '+new'), SemesterNew),
             (Subject, '+index', SubjectView),
             (Subject, '+edit', SubjectEdit),
             (Subject, '+new-offering', SubjectOfferingNew),
             (Semester, '+edit', SemesterEdit),
             (Offering, '+index', OfferingView),
             (Offering, '+edit', OfferingEdit),
             (Offering, '+clone-worksheets', OfferingCloneWorksheets),
             (Offering, ('+enrolments', '+index'), EnrolmentsView),
             (Offering, ('+enrolments', '+new'), EnrolView),
             (Enrolment, '+edit', EnrolmentEdit),
             (Enrolment, '+delete', EnrolmentDelete),
             (Offering, ('+projects', '+index'), OfferingProjectsView),
             (Offering, ('+projects', '+new-set'), ProjectSetNew),
             (ProjectSet, '+edit', ProjectSetEdit),
             (ProjectSet, '+new', ProjectNew),
             (Project, '+index', ProjectView),
             (Project, '+edit', ProjectEdit),
             (Project, '+delete', ProjectDelete),
             (Project, ('+export', 'project-export.sh'),
                ProjectBashExportView),
             ]

    breadcrumbs = {Subject: SubjectBreadcrumb,
                   Offering: OfferingBreadcrumb,
                   User: UserBreadcrumb,
                   Project: ProjectBreadcrumb,
                   Enrolment: EnrolmentBreadcrumb,
                   }

    tabs = [
        ('subjects', 'Subjects',
         'View subject content and complete worksheets',
         'subjects.png', 'subjects', 5)
    ]

    media = 'subject-media'
