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

# Author: Matt Giuca, Will Grant

"""Database utilities and content classes.

This module provides all of the classes which map to database tables.
It also provides miscellaneous utility functions for database interaction.
"""

import hashlib
import datetime
import os
import urlparse
import urllib

from storm.locals import create_database, Store, Int, Unicode, DateTime, \
                         Reference, ReferenceSet, Bool, Storm, Desc
from storm.expr import Select, Max
from storm.exceptions import NotOneError, IntegrityError

from ivle.worksheet.rst import rst

__all__ = ['get_store',
            'User',
            'Subject', 'Semester', 'Offering', 'Enrolment',
            'ProjectSet', 'Project', 'ProjectGroup', 'ProjectGroupMembership',
            'Assessed', 'ProjectSubmission', 'ProjectExtension',
            'Exercise', 'Worksheet', 'WorksheetExercise',
            'ExerciseSave', 'ExerciseAttempt',
            'TestCase', 'TestSuite', 'TestSuiteVar'
        ]

def _kwarg_init(self, **kwargs):
    for k,v in kwargs.items():
        if k.startswith('_') or not hasattr(self.__class__, k):
            raise TypeError("%s got an unexpected keyword argument '%s'"
                % (self.__class__.__name__, k))
        setattr(self, k, v)

def get_conn_string(config):
    """Create a Storm connection string to the IVLE database

    @param config: The IVLE configuration.
    """

    clusterstr = ''
    if config['database']['username']:
        clusterstr += config['database']['username']
        if config['database']['password']:
            clusterstr += ':' + config['database']['password']
        clusterstr += '@'

    host = config['database']['host'] or 'localhost'
    port = config['database']['port'] or 5432

    clusterstr += '%s:%d' % (host, port)

    return "postgres://%s/%s" % (clusterstr, config['database']['name'])

def get_store(config):
    """Create a Storm store connected to the IVLE database.

    @param config: The IVLE configuration.
    """
    return Store(create_database(get_conn_string(config)))

# USERS #

class User(Storm):
    """An IVLE user account."""
    __storm_table__ = "login"

    id = Int(primary=True, name="loginid")
    login = Unicode()
    passhash = Unicode()
    state = Unicode()
    admin = Bool()
    unixid = Int()
    nick = Unicode()
    pass_exp = DateTime()
    acct_exp = DateTime()
    last_login = DateTime()
    svn_pass = Unicode()
    email = Unicode()
    fullname = Unicode()
    studentid = Unicode()
    settings = Unicode()

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s '%s'>" % (type(self).__name__, self.login)

    def authenticate(self, password):
        """Validate a given password against this user.

        Returns True if the given password matches the password hash for this
        User, False if it doesn't match, and None if there is no hash for the
        user.
        """
        if self.passhash is None:
            return None
        return self.hash_password(password) == self.passhash

    @property
    def display_name(self):
        """Returns the "nice name" of the user or group."""
        return self.fullname

    @property
    def short_name(self):
        """Returns the database "identifier" name of the user or group."""
        return self.login

    @property
    def password_expired(self):
        fieldval = self.pass_exp
        return fieldval is not None and datetime.datetime.now() > fieldval

    @property
    def account_expired(self):
        fieldval = self.acct_exp
        return fieldval is not None and datetime.datetime.now() > fieldval

    @property
    def valid(self):
        return self.state == 'enabled' and not self.account_expired

    def _get_enrolments(self, justactive):
        return Store.of(self).find(Enrolment,
            Enrolment.user_id == self.id,
            (Enrolment.active == True) if justactive else True,
            Enrolment.offering_id == Offering.id,
            Offering.semester_id == Semester.id,
            Offering.subject_id == Subject.id).order_by(
                Desc(Semester.year),
                Desc(Semester.display_name),
                Desc(Subject.code)
            )

    def _set_password(self, password):
        if password is None:
            self.passhash = None
        else:
            self.passhash = unicode(User.hash_password(password))
    password = property(fset=_set_password)

    @property
    def subjects(self):
        return Store.of(self).find(Subject,
            Enrolment.user_id == self.id,
            Enrolment.active == True,
            Offering.id == Enrolment.offering_id,
            Subject.id == Offering.subject_id).config(distinct=True)

    # TODO: Invitations should be listed too?
    def get_groups(self, offering=None):
        """Get groups of which this user is a member.

        @param offering: An optional offering to restrict the search to.
        """
        preds = [
            ProjectGroupMembership.user_id == self.id,
            ProjectGroup.id == ProjectGroupMembership.project_group_id,
        ]
        if offering:
            preds.extend([
                ProjectSet.offering_id == offering.id,
                ProjectGroup.project_set_id == ProjectSet.id,
            ])
        return Store.of(self).find(ProjectGroup, *preds)

    @property
    def groups(self):
        return self.get_groups()

    @property
    def active_enrolments(self):
        '''A sanely ordered list of the user's active enrolments.'''
        return self._get_enrolments(True)

    @property
    def enrolments(self):
        '''A sanely ordered list of all of the user's enrolments.'''
        return self._get_enrolments(False) 

    def get_projects(self, offering=None, active_only=True):
        """Find projects that the user can submit.

        This will include projects for offerings in which the user is
        enrolled, as long as the project is not in a project set which has
        groups (ie. if maximum number of group members is 0).

        @param active_only: Whether to only search active offerings.
        @param offering: An optional offering to restrict the search to.
        """
        return Store.of(self).find(Project,
            Project.project_set_id == ProjectSet.id,
            ProjectSet.max_students_per_group == None,
            ProjectSet.offering_id == Offering.id,
            (offering is None) or (Offering.id == offering.id),
            Semester.id == Offering.semester_id,
            (not active_only) or (Semester.state == u'current'),
            Enrolment.offering_id == Offering.id,
            Enrolment.user_id == self.id,
            Enrolment.active == True)

    @staticmethod
    def hash_password(password):
        """Hash a password with MD5."""
        return hashlib.md5(password).hexdigest()

    @classmethod
    def get_by_login(cls, store, login):
        """Find a user in a store by login name."""
        return store.find(cls, cls.login == unicode(login)).one()

    def get_svn_url(self, config):
        """Get the subversion repository URL for this user or group."""
        url = config['urls']['svn_addr']
        path = 'users/%s' % self.login
        return urlparse.urljoin(url, path)

    def get_permissions(self, user, config):
        """Determine privileges held by a user over this object.

        If the user requesting privileges is this user or an admin,
        they may do everything. Otherwise they may do nothing.
        """
        if user and user.admin or user is self:
            return set(['view_public', 'view', 'edit', 'submit_project'])
        else:
            return set(['view_public'])

# SUBJECTS AND ENROLMENTS #

class Subject(Storm):
    """A subject (or course) which is run in some semesters."""

    __storm_table__ = "subject"

    id = Int(primary=True, name="subjectid")
    code = Unicode(name="subj_code")
    name = Unicode(name="subj_name")
    short_name = Unicode(name="subj_short_name")

    offerings = ReferenceSet(id, 'Offering.subject_id')

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s '%s'>" % (type(self).__name__, self.short_name)

    def get_permissions(self, user, config):
        """Determine privileges held by a user over this object.

        If the user requesting privileges is an admin, they may edit.
        Otherwise they may only read.
        """
        perms = set()
        if user is not None:
            perms.add('view')
            if user.admin:
                perms.add('edit')
        return perms

    def active_offerings(self):
        """Find active offerings for this subject.

        Return a sequence of currently active offerings for this subject
        (offerings whose semester.state is "current"). There should be 0 or 1
        elements in this sequence, but it's possible there are more.
        """
        return self.offerings.find(Offering.semester_id == Semester.id,
                                   Semester.state == u'current')

    def offering_for_semester(self, year, semester):
        """Get the offering for the given year/semester, or None.

        @param year: A string representation of the year.
        @param semester: A string representation of the semester.
        """
        return self.offerings.find(Offering.semester_id == Semester.id,
                               Semester.year == unicode(year),
                               Semester.url_name == unicode(semester)).one()

class Semester(Storm):
    """A semester in which subjects can be run."""

    __storm_table__ = "semester"

    id = Int(primary=True, name="semesterid")
    year = Unicode()
    code = Unicode()
    url_name = Unicode()
    display_name = Unicode()
    state = Unicode()

    offerings = ReferenceSet(id, 'Offering.semester_id')
    enrolments = ReferenceSet(id,
                              'Offering.semester_id',
                              'Offering.id',
                              'Enrolment.offering_id')

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s/%s>" % (type(self).__name__, self.year, self.code)

class Offering(Storm):
    """An offering of a subject in a particular semester."""

    __storm_table__ = "offering"

    id = Int(primary=True, name="offeringid")
    subject_id = Int(name="subject")
    subject = Reference(subject_id, Subject.id)
    semester_id = Int(name="semesterid")
    semester = Reference(semester_id, Semester.id)
    description = Unicode()
    url = Unicode()
    show_worksheet_marks = Bool()
    worksheet_cutoff = DateTime()
    groups_student_permissions = Unicode()

    enrolments = ReferenceSet(id, 'Enrolment.offering_id')
    members = ReferenceSet(id,
                           'Enrolment.offering_id',
                           'Enrolment.user_id',
                           'User.id')
    project_sets = ReferenceSet(id, 'ProjectSet.offering_id')
    projects = ReferenceSet(id,
                            'ProjectSet.offering_id',
                            'ProjectSet.id',
                            'Project.project_set_id')

    worksheets = ReferenceSet(id, 
        'Worksheet.offering_id', 
        order_by="seq_no"
    )

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %r in %r>" % (type(self).__name__, self.subject,
                                  self.semester)

    def enrol(self, user, role=u'student'):
        """Enrol a user in this offering.

        Enrolments handle both the staff and student cases. The role controls
        the privileges granted by this enrolment.
        """
        enrolment = Store.of(self).find(Enrolment,
                               Enrolment.user_id == user.id,
                               Enrolment.offering_id == self.id).one()

        if enrolment is None:
            enrolment = Enrolment(user=user, offering=self)
            self.enrolments.add(enrolment)

        enrolment.active = True
        enrolment.role = role

    def unenrol(self, user):
        '''Unenrol a user from this offering.'''
        enrolment = Store.of(self).find(Enrolment,
                               Enrolment.user_id == user.id,
                               Enrolment.offering_id == self.id).one()
        Store.of(enrolment).remove(enrolment)

    def get_permissions(self, user, config):
        perms = set()
        if user is not None:
            enrolment = self.get_enrolment(user)
            if enrolment or user.admin:
                perms.add('view')
            if enrolment and enrolment.role == u'tutor':
                perms.add('view_project_submissions')
                # Site-specific policy on the role of tutors
                if config['policy']['tutors_can_enrol_students']:
                    perms.add('enrol')
                    perms.add('enrol_student')
                if config['policy']['tutors_can_edit_worksheets']:
                    perms.add('edit_worksheets')
                if config['policy']['tutors_can_admin_groups']:
                    perms.add('admin_groups')
            if (enrolment and enrolment.role in (u'lecturer')) or user.admin:
                perms.add('view_project_submissions')
                perms.add('admin_groups')
                perms.add('edit_worksheets')
                perms.add('view_worksheet_marks')
                perms.add('edit')           # Can edit projects & details
                perms.add('enrol')          # Can see enrolment screen at all
                perms.add('enrol_student')  # Can enrol students
                perms.add('enrol_tutor')    # Can enrol tutors
            if user.admin:
                perms.add('enrol_lecturer') # Can enrol lecturers
        return perms

    def get_enrolment(self, user):
        """Find the user's enrolment in this offering."""
        try:
            enrolment = self.enrolments.find(user=user).one()
        except NotOneError:
            enrolment = None

        return enrolment

    def get_members_by_role(self, role):
        return Store.of(self).find(User,
                Enrolment.user_id == User.id,
                Enrolment.offering_id == self.id,
                Enrolment.role == role
                ).order_by(User.login)

    @property
    def students(self):
        return self.get_members_by_role(u'student')

    def get_open_projects_for_user(self, user):
        """Find all projects currently open to submissions by a user."""
        # XXX: Respect extensions.
        return self.projects.find(Project.deadline > datetime.datetime.now())

    def has_worksheet_cutoff_passed(self, user):
        """Check whether the worksheet cutoff has passed.
        A user is required, in case we support extensions.
        """
        if self.worksheet_cutoff is None:
            return False
        else:
            return self.worksheet_cutoff < datetime.datetime.now()

    def clone_worksheets(self, source):
        """Clone all worksheets from the specified source to this offering."""
        import ivle.worksheet.utils
        for worksheet in source.worksheets:
            newws = Worksheet()
            newws.seq_no = worksheet.seq_no
            newws.identifier = worksheet.identifier
            newws.name = worksheet.name
            newws.assessable = worksheet.assessable
            newws.published = worksheet.published
            newws.data = worksheet.data
            newws.format = worksheet.format
            newws.offering = self
            Store.of(self).add(newws)
            ivle.worksheet.utils.update_exerciselist(newws)


class Enrolment(Storm):
    """An enrolment of a user in an offering.

    This represents the roles of both staff and students.
    """

    __storm_table__ = "enrolment"
    __storm_primary__ = "user_id", "offering_id"

    user_id = Int(name="loginid")
    user = Reference(user_id, User.id)
    offering_id = Int(name="offeringid")
    offering = Reference(offering_id, Offering.id)
    role = Unicode()
    notes = Unicode()
    active = Bool()

    @property
    def groups(self):
        return Store.of(self).find(ProjectGroup,
                ProjectSet.offering_id == self.offering.id,
                ProjectGroup.project_set_id == ProjectSet.id,
                ProjectGroupMembership.project_group_id == ProjectGroup.id,
                ProjectGroupMembership.user_id == self.user.id)

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %r in %r>" % (type(self).__name__, self.user,
                                  self.offering)

    def get_permissions(self, user, config):
        # A user can edit any enrolment that they could have created.
        perms = set()
        if ('enrol_' + str(self.role)) in self.offering.get_permissions(
            user, config):
            perms.add('edit')
        return perms

    def delete(self):
        """Delete this enrolment."""
        Store.of(self).remove(self)


# PROJECTS #

class ProjectSet(Storm):
    """A set of projects that share common groups.

    Each student project group is attached to a project set. The group is
    valid for all projects in the group's set.
    """

    __storm_table__ = "project_set"

    id = Int(name="projectsetid", primary=True)
    offering_id = Int(name="offeringid")
    offering = Reference(offering_id, Offering.id)
    max_students_per_group = Int()

    projects = ReferenceSet(id, 'Project.project_set_id')
    project_groups = ReferenceSet(id, 'ProjectGroup.project_set_id')

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %d in %r>" % (type(self).__name__, self.id,
                                  self.offering)

    def get_permissions(self, user, config):
        return self.offering.get_permissions(user, config)

    def get_groups_for_user(self, user):
        """List all groups in this offering of which the user is a member."""
        assert self.is_group
        return Store.of(self).find(
            ProjectGroup,
            ProjectGroupMembership.user_id == user.id,
            ProjectGroupMembership.project_group_id == ProjectGroup.id,
            ProjectGroup.project_set_id == self.id)

    def get_submission_principal(self, user):
        """Get the principal on behalf of which the user can submit.

        If this is a solo project set, the given user is returned. If
        the user is a member of exactly one group, all the group is
        returned. Otherwise, None is returned.
        """
        if self.is_group:
            groups = self.get_groups_for_user(user)
            if groups.count() == 1:
                return groups.one()
            else:
                return None
        else:
            return user

    @property
    def is_group(self):
        return self.max_students_per_group is not None

    @property
    def assigned(self):
        """Get the entities (groups or users) assigned to submit this project.

        This will be a Storm ResultSet.
        """
        #If its a solo project, return everyone in offering
        if self.is_group:
            return self.project_groups
        else:
            return self.offering.students

class DeadlinePassed(Exception):
    """An exception indicating that a project cannot be submitted because the
    deadline has passed."""
    def __init__(self):
        pass
    def __str__(self):
        return "The project deadline has passed"

class Project(Storm):
    """A student project for which submissions can be made."""

    __storm_table__ = "project"

    id = Int(name="projectid", primary=True)
    name = Unicode()
    short_name = Unicode()
    synopsis = Unicode()
    url = Unicode()
    project_set_id = Int(name="projectsetid")
    project_set = Reference(project_set_id, ProjectSet.id)
    deadline = DateTime()

    assesseds = ReferenceSet(id, 'Assessed.project_id')
    submissions = ReferenceSet(id,
                               'Assessed.project_id',
                               'Assessed.id',
                               'ProjectSubmission.assessed_id')

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s '%s' in %r>" % (type(self).__name__, self.short_name,
                                  self.project_set.offering)

    def can_submit(self, principal, user, late=False):
        """
        @param late: If True, does not take the deadline into account.
        """
        return (self in principal.get_projects() and
                (late or not self.has_deadline_passed(user)))

    def submit(self, principal, path, revision, who, late=False):
        """Submit a Subversion path and revision to a project.

        @param principal: The owner of the Subversion repository, and the
                          entity on behalf of whom the submission is being made
        @param path: A path within that repository to submit.
        @param revision: The revision of that path to submit.
        @param who: The user who is actually making the submission.
        @param late: If True, will not raise a DeadlinePassed exception even
            after the deadline. (Default False.)
        """

        if not self.can_submit(principal, who, late=late):
            raise DeadlinePassed()

        a = Assessed.get(Store.of(self), principal, self)
        ps = ProjectSubmission()
        # Raise SubmissionError if the path is illegal
        ps.path = ProjectSubmission.test_and_normalise_path(path)
        ps.revision = revision
        ps.date_submitted = datetime.datetime.now()
        ps.assessed = a
        ps.submitter = who

        return ps

    def get_permissions(self, user, config):
        return self.project_set.offering.get_permissions(user, config)

    @property
    def latest_submissions(self):
        """Return the latest submission for each Assessed."""
        return Store.of(self).find(ProjectSubmission,
            Assessed.project_id == self.id,
            ProjectSubmission.assessed_id == Assessed.id,
            ProjectSubmission.date_submitted == Select(
                    Max(ProjectSubmission.date_submitted),
                    ProjectSubmission.assessed_id == Assessed.id,
                    tables=ProjectSubmission
            )
        )

    def has_deadline_passed(self, user):
        """Check whether the deadline has passed."""
        # XXX: Need to respect extensions.
        return self.deadline < datetime.datetime.now()

    def get_submissions_for_principal(self, principal):
        """Fetch a ResultSet of all submissions by a particular principal."""
        assessed = Assessed.get(Store.of(self), principal, self)
        if assessed is None:
            return
        return assessed.submissions

    @property
    def can_delete(self):
        """Can only delete if there are no submissions."""
        return self.submissions.count() == 0

    def delete(self):
        """Delete the project. Fails if can_delete is False."""
        if not self.can_delete:
            raise IntegrityError()
        for assessed in self.assesseds:
            assessed.delete()
        Store.of(self).remove(self)

class ProjectGroup(Storm):
    """A group of students working together on a project."""

    __storm_table__ = "project_group"

    id = Int(name="groupid", primary=True)
    name = Unicode(name="groupnm")
    project_set_id = Int(name="projectsetid")
    project_set = Reference(project_set_id, ProjectSet.id)
    nick = Unicode()
    created_by_id = Int(name="createdby")
    created_by = Reference(created_by_id, User.id)
    epoch = DateTime()

    members = ReferenceSet(id,
                           "ProjectGroupMembership.project_group_id",
                           "ProjectGroupMembership.user_id",
                           "User.id")

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s in %r>" % (type(self).__name__, self.name,
                                  self.project_set.offering)

    @property
    def display_name(self):
        """Returns the "nice name" of the user or group."""
        return self.nick

    @property
    def short_name(self):
        """Returns the database "identifier" name of the user or group."""
        return self.name

    def get_projects(self, offering=None, active_only=True):
        '''Find projects that the group can submit.

        This will include projects in the project set which owns this group,
        unless the project set disallows groups (in which case none will be
        returned).

        @param active_only: Whether to only search active offerings.
        @param offering: An optional offering to restrict the search to.
        '''
        return Store.of(self).find(Project,
            Project.project_set_id == ProjectSet.id,
            ProjectSet.id == self.project_set.id,
            ProjectSet.max_students_per_group != None,
            ProjectSet.offering_id == Offering.id,
            (offering is None) or (Offering.id == offering.id),
            Semester.id == Offering.semester_id,
            (not active_only) or (Semester.state == u'current'))

    def get_svn_url(self, config):
        """Get the subversion repository URL for this user or group."""
        url = config['urls']['svn_addr']
        path = 'groups/%s_%s_%s_%s' % (
                self.project_set.offering.subject.short_name,
                self.project_set.offering.semester.year,
                self.project_set.offering.semester.url_name,
                self.name
                )
        return urlparse.urljoin(url, path)

    def get_permissions(self, user, config):
        if user.admin or user in self.members:
            return set(['submit_project'])
        else:
            return set()

class ProjectGroupMembership(Storm):
    """A student's membership in a project group."""

    __storm_table__ = "group_member"
    __storm_primary__ = "user_id", "project_group_id"

    user_id = Int(name="loginid")
    user = Reference(user_id, User.id)
    project_group_id = Int(name="groupid")
    project_group = Reference(project_group_id, ProjectGroup.id)

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %r in %r>" % (type(self).__name__, self.user,
                                  self.project_group)

class Assessed(Storm):
    """A composite of a user or group combined with a project.

    Each project submission and extension refers to an Assessed. It is the
    sole specifier of the repository and project.
    """

    __storm_table__ = "assessed"

    id = Int(name="assessedid", primary=True)
    user_id = Int(name="loginid")
    user = Reference(user_id, User.id)
    project_group_id = Int(name="groupid")
    project_group = Reference(project_group_id, ProjectGroup.id)

    project_id = Int(name="projectid")
    project = Reference(project_id, Project.id)

    extensions = ReferenceSet(id, 'ProjectExtension.assessed_id')
    submissions = ReferenceSet(
        id, 'ProjectSubmission.assessed_id', order_by='date_submitted')

    def __repr__(self):
        return "<%s %r in %r>" % (type(self).__name__,
            self.user or self.project_group, self.project)

    @property
    def is_group(self):
        """True if the Assessed is a group, False if it is a user."""
        return self.project_group is not None

    @property
    def principal(self):
        return self.project_group or self.user

    @property
    def checkout_location(self):
        """Returns the location of the Subversion workspace for this piece of
        assessment, relative to each group member's home directory."""
        subjectname = self.project.project_set.offering.subject.short_name
        if self.is_group:
            checkout_dir_name = self.principal.short_name
        else:
            checkout_dir_name = "mywork"
        return subjectname + "/" + checkout_dir_name

    @classmethod
    def get(cls, store, principal, project):
        """Find or create an Assessed for the given user or group and project.

        @param principal: The user or group.
        @param project: The project.
        """
        t = type(principal)
        if t not in (User, ProjectGroup):
            raise AssertionError('principal must be User or ProjectGroup')

        a = store.find(cls,
            (t is User) or (cls.project_group_id == principal.id),
            (t is ProjectGroup) or (cls.user_id == principal.id),
            cls.project_id == project.id).one()

        if a is None:
            a = cls()
            if t is User:
                a.user = principal
            else:
                a.project_group = principal
            a.project = project
            store.add(a)

        return a

    def delete(self):
        """Delete the assessed. Fails if there are any submissions. Deletes
        extensions."""
        if self.submissions.count() > 0:
            raise IntegrityError()
        for extension in self.extensions:
            extension.delete()
        Store.of(self).remove(self)

class ProjectExtension(Storm):
    """An extension granted to a user or group on a particular project.

    The user or group and project are specified by the Assessed.
    """

    __storm_table__ = "project_extension"

    id = Int(name="extensionid", primary=True)
    assessed_id = Int(name="assessedid")
    assessed = Reference(assessed_id, Assessed.id)
    days = Int()
    approver_id = Int(name="approver")
    approver = Reference(approver_id, User.id)
    notes = Unicode()

    def delete(self):
        """Delete the extension."""
        Store.of(self).remove(self)

class SubmissionError(Exception):
    """Denotes a validation error during submission."""
    pass

class ProjectSubmission(Storm):
    """A submission from a user or group repository to a particular project.

    The content of a submission is a single path and revision inside a
    repository. The repository is that owned by the submission's user and
    group, while the path and revision are explicit.

    The user or group and project are specified by the Assessed.
    """

    __storm_table__ = "project_submission"

    id = Int(name="submissionid", primary=True)
    assessed_id = Int(name="assessedid")
    assessed = Reference(assessed_id, Assessed.id)
    path = Unicode()
    revision = Int()
    submitter_id = Int(name="submitter")
    submitter = Reference(submitter_id, User.id)
    date_submitted = DateTime()

    def get_verify_url(self, user):
        """Get the URL for verifying this submission, within the account of
        the given user."""
        # If this is a solo project, then self.path will be prefixed with the
        # subject name. Remove the first path segment.
        submitpath = self.path[1:] if self.path[:1] == '/' else self.path
        if not self.assessed.is_group:
            if '/' in submitpath:
                submitpath = submitpath.split('/', 1)[1]
            else:
                submitpath = ''
        return "/files/%s/%s/%s?r=%d" % (user.login,
            self.assessed.checkout_location, submitpath, self.revision)

    def get_svn_url(self, config):
        """Get subversion URL for this submission"""
        princ = self.assessed.principal
        base = princ.get_svn_url(config)
        if self.path.startswith(os.sep):
            return os.path.join(base,
                    urllib.quote(self.path[1:].encode('utf-8')))
        else:
            return os.path.join(base, urllib.quote(self.path.encode('utf-8')))

    def get_svn_export_command(self, req):
        """Returns a Unix shell command to export a submission"""
        svn_url = self.get_svn_url(req.config)
        _, ext = os.path.splitext(svn_url)
        username = (req.user.login if req.user.login.isalnum() else
                "'%s'"%req.user.login)
        # Export to a file or directory relative to the current directory,
        # with the student's login name, appended with the submitted file's
        # extension, if any
        export_path = self.assessed.principal.short_name + ext
        return "svn export --username %s -r%d '%s' %s"%(req.user.login,
                self.revision, svn_url, export_path)

    @staticmethod
    def test_and_normalise_path(path):
        """Test that path is valid, and normalise it. This prevents possible
        injections using malicious paths.
        Returns the updated path, if successful.
        Raises SubmissionError if invalid.
        """
        # Ensure the path is absolute to prevent being tacked onto working
        # directories.
        # Prevent '\n' because it will break all sorts of things.
        # Prevent '[' and ']' because they can be used to inject into the
        # svn.conf.
        # Normalise to avoid resulting in ".." path segments.
        if not os.path.isabs(path):
            raise SubmissionError("Path is not absolute")
        if any(c in path for c in "\n[]"):
            raise SubmissionError("Path must not contain '\\n', '[' or ']'")
        return os.path.normpath(path)

    @property
    def late(self):
        """True if the project was submitted late."""
        return self.days_late > 0

    @property
    def days_late(self):
        """The number of days the project was submitted late (rounded up), or
        0 if on-time."""
        # XXX: Need to respect extensions.
        return max(0,
            (self.date_submitted - self.assessed.project.deadline).days + 1)

# WORKSHEETS AND EXERCISES #

class Exercise(Storm):
    """An exercise for students to complete in a worksheet.

    An exercise may be present in any number of worksheets.
    """

    __storm_table__ = "exercise"
    id = Unicode(primary=True, name="identifier")
    name = Unicode()
    description = Unicode()
    _description_xhtml_cache = Unicode(name='description_xhtml_cache')
    partial = Unicode()
    solution = Unicode()
    include = Unicode()
    num_rows = Int()

    worksheet_exercises =  ReferenceSet(id,
        'WorksheetExercise.exercise_id')

    worksheets = ReferenceSet(id,
        'WorksheetExercise.exercise_id',
        'WorksheetExercise.worksheet_id',
        'Worksheet.id'
    )

    test_suites = ReferenceSet(id, 
        'TestSuite.exercise_id',
        order_by='seq_no')

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self.name)

    def get_permissions(self, user, config):
        return self.global_permissions(user, config)

    @staticmethod
    def global_permissions(user, config):
        """Gets the set of permissions this user has over *all* exercises.
        This is used to determine who may view the exercises list, and create
        new exercises."""
        perms = set()
        roles = set()
        if user is not None:
            if user.admin:
                perms.add('edit')
                perms.add('view')
            elif u'lecturer' in set((e.role for e in user.active_enrolments)):
                perms.add('edit')
                perms.add('view')
            elif (config['policy']['tutors_can_edit_worksheets']
            and u'tutor' in set((e.role for e in user.active_enrolments))):
                # Site-specific policy on the role of tutors
                perms.add('edit')
                perms.add('view')

        return perms

    def _cache_description_xhtml(self, invalidate=False):
        # Don't regenerate an existing cache unless forced.
        if self._description_xhtml_cache is not None and not invalidate:
            return

        if self.description:
            self._description_xhtml_cache = rst(self.description)
        else:
            self._description_xhtml_cache = None

    @property
    def description_xhtml(self):
        """The XHTML exercise description, converted from reStructuredText."""
        self._cache_description_xhtml()
        return self._description_xhtml_cache

    def set_description(self, description):
        self.description = description
        self._cache_description_xhtml(invalidate=True)

    def delete(self):
        """Deletes the exercise, providing it has no associated worksheets."""
        if (self.worksheet_exercises.count() > 0):
            raise IntegrityError()
        for suite in self.test_suites:
            suite.delete()
        Store.of(self).remove(self)

class Worksheet(Storm):
    """A worksheet with exercises for students to complete.

    Worksheets are owned by offerings.
    """

    __storm_table__ = "worksheet"

    id = Int(primary=True, name="worksheetid")
    offering_id = Int(name="offeringid")
    identifier = Unicode()
    name = Unicode()
    assessable = Bool()
    published = Bool()
    data = Unicode()
    _data_xhtml_cache = Unicode(name='data_xhtml_cache')
    seq_no = Int()
    format = Unicode()

    attempts = ReferenceSet(id, "ExerciseAttempt.worksheetid")
    offering = Reference(offering_id, 'Offering.id')

    all_worksheet_exercises = ReferenceSet(id,
        'WorksheetExercise.worksheet_id')

    # Use worksheet_exercises to get access to the *active* WorksheetExercise
    # objects binding worksheets to exercises. This is required to access the
    # "optional" field.

    @property
    def worksheet_exercises(self):
        return self.all_worksheet_exercises.find(active=True)

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self.name)

    def remove_all_exercises(self):
        """Remove all exercises from this worksheet.

        This does not delete the exercises themselves. It just removes them
        from the worksheet.
        """
        store = Store.of(self)
        for ws_ex in self.all_worksheet_exercises:
            if ws_ex.saves.count() > 0 or ws_ex.attempts.count() > 0:
                raise IntegrityError()
        store.find(WorksheetExercise,
            WorksheetExercise.worksheet == self).remove()

    def get_permissions(self, user, config):
        offering_perms = self.offering.get_permissions(user, config)

        perms = set()

        # Anybody who can view an offering can view a published
        # worksheet.
        if 'view' in offering_perms and self.published:
            perms.add('view')

        # Any worksheet editors can both view and edit.
        if 'edit_worksheets' in offering_perms:
            perms.add('view')
            perms.add('edit')

        return perms

    def _cache_data_xhtml(self, invalidate=False):
        # Don't regenerate an existing cache unless forced.
        if self._data_xhtml_cache is not None and not invalidate:
            return

        if self.format == u'rst':
            self._data_xhtml_cache = rst(self.data)
        else:
            self._data_xhtml_cache = None

    @property
    def data_xhtml(self):
        """The XHTML of this worksheet, converted from rST if required."""
        # Update the rST -> XHTML cache, if required.
        self._cache_data_xhtml()

        if self.format == u'rst':
            return self._data_xhtml_cache
        else:
            return self.data

    def set_data(self, data):
        self.data = data
        self._cache_data_xhtml(invalidate=True)

    def delete(self):
        """Deletes the worksheet, provided it has no attempts on any exercises.

        Returns True if delete succeeded, or False if this worksheet has
        attempts attached."""
        for ws_ex in self.all_worksheet_exercises:
            if ws_ex.saves.count() > 0 or ws_ex.attempts.count() > 0:
                raise IntegrityError()

        self.remove_all_exercises()
        Store.of(self).remove(self)

class WorksheetExercise(Storm):
    """A link between a worksheet and one of its exercises.

    These may be marked optional, in which case the exercise does not count
    for marking purposes. The sequence number is used to order the worksheet
    ToC.
    """

    __storm_table__ = "worksheet_exercise"

    id = Int(primary=True, name="ws_ex_id")

    worksheet_id = Int(name="worksheetid")
    worksheet = Reference(worksheet_id, Worksheet.id)
    exercise_id = Unicode(name="exerciseid")
    exercise = Reference(exercise_id, Exercise.id)
    optional = Bool()
    active = Bool()
    seq_no = Int()

    saves = ReferenceSet(id, "ExerciseSave.ws_ex_id")
    attempts = ReferenceSet(id, "ExerciseAttempt.ws_ex_id")

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s in %s>" % (type(self).__name__, self.exercise.name,
                                  self.worksheet.identifier)

    def get_permissions(self, user, config):
        return self.worksheet.get_permissions(user, config)


class ExerciseSave(Storm):
    """A potential exercise solution submitted by a user for storage.

    This is not an actual tested attempt at an exercise, it's just a save of
    the editing session.
    """

    __storm_table__ = "exercise_save"
    __storm_primary__ = "ws_ex_id", "user_id"

    ws_ex_id = Int(name="ws_ex_id")
    worksheet_exercise = Reference(ws_ex_id, "WorksheetExercise.id")

    user_id = Int(name="loginid")
    user = Reference(user_id, User.id)
    date = DateTime()
    text = Unicode()

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s by %s at %s>" % (type(self).__name__,
            self.worksheet_exercise.exercise.name, self.user.login,
            self.date.strftime("%c"))

class ExerciseAttempt(ExerciseSave):
    """An attempt at solving an exercise.

    This is a special case of ExerciseSave, used when the user submits a
    candidate solution. Like an ExerciseSave, it constitutes exercise solution
    data.

    In addition, it contains information about the result of the submission:

     - complete - True if this submission was successful, rendering this
                  exercise complete for this user in this worksheet.
     - active   - True if this submission is "active" (usually true).
                  Submissions may be de-activated by privileged users for
                  special reasons, and then they won't count (either as a
                  penalty or success), but will still be stored.
    """

    __storm_table__ = "exercise_attempt"
    __storm_primary__ = "ws_ex_id", "user_id", "date"

    # The "text" field is the same but has a different name in the DB table
    # for some reason.
    text = Unicode(name="attempt")
    complete = Bool()
    active = Bool()

    def get_permissions(self, user, config):
        return set(['view']) if user is self.user else set()

class TestSuite(Storm):
    """A container to group an exercise's test cases.

    The test suite contains some information on how to test. The function to
    test, variables to set and stdin data are stored here.
    """

    __storm_table__ = "test_suite"
    __storm_primary__ = "exercise_id", "suiteid"

    suiteid = Int()
    exercise_id = Unicode(name="exerciseid")
    description = Unicode()
    seq_no = Int()
    function = Unicode()
    stdin = Unicode()
    exercise = Reference(exercise_id, Exercise.id)
    test_cases = ReferenceSet(suiteid, 'TestCase.suiteid', order_by="seq_no")
    variables = ReferenceSet(suiteid, 'TestSuiteVar.suiteid', order_by='arg_no')

    def delete(self):
        """Delete this suite, without asking questions."""
        for variable in self.variables:
            variable.delete()
        for test_case in self.test_cases:
            test_case.delete()
        Store.of(self).remove(self)

class TestCase(Storm):
    """A container for actual tests (see TestCasePart), inside a test suite.

    It is the lowest level shown to students on their pass/fail status."""

    __storm_table__ = "test_case"
    __storm_primary__ = "testid", "suiteid"

    testid = Int()
    suiteid = Int()
    suite = Reference(suiteid, "TestSuite.suiteid")
    passmsg = Unicode()
    failmsg = Unicode()
    test_default = Unicode() # Currently unused - only used for file matching.
    seq_no = Int()

    parts = ReferenceSet(testid, "TestCasePart.testid")

    __init__ = _kwarg_init

    def delete(self):
        for part in self.parts:
            part.delete()
        Store.of(self).remove(self)

class TestSuiteVar(Storm):
    """A variable used by an exercise test suite.

    This may represent a function argument or a normal variable.
    """

    __storm_table__ = "suite_variable"
    __storm_primary__ = "varid"

    varid = Int()
    suiteid = Int()
    var_name = Unicode()
    var_value = Unicode()
    var_type = Unicode()
    arg_no = Int()

    suite = Reference(suiteid, "TestSuite.suiteid")

    __init__ = _kwarg_init

    def delete(self):
        Store.of(self).remove(self)

class TestCasePart(Storm):
    """An actual piece of code to test an exercise solution."""

    __storm_table__ = "test_case_part"
    __storm_primary__ = "partid"

    partid = Int()
    testid = Int()

    part_type = Unicode()
    test_type = Unicode()
    data = Unicode()
    filename = Unicode()

    test = Reference(testid, "TestCase.testid")

    __init__ = _kwarg_init

    def delete(self):
        Store.of(self).remove(self)
