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

"""
Database Classes and Utilities for Storm ORM

This module provides all of the classes which map to database tables.
It also provides miscellaneous utility functions for database interaction.
"""

import md5
import datetime

from storm.locals import create_database, Store, Int, Unicode, DateTime, \
                         Reference, ReferenceSet, Bool, Storm, Desc
from storm.exceptions import NotOneError, IntegrityError

import ivle.conf
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

def get_conn_string():
    """
    Returns the Storm connection string, generated from the conf file.
    """

    clusterstr = ''
    if ivle.conf.db_user:
        clusterstr += ivle.conf.db_user
        if ivle.conf.db_password:
            clusterstr += ':' + ivle.conf.db_password
        clusterstr += '@'

    host = ivle.conf.db_host or 'localhost'
    port = ivle.conf.db_port or 5432

    clusterstr += '%s:%d' % (host, port)

    return "postgres://%s/%s" % (clusterstr, ivle.conf.db_dbname)

def get_store():
    """
    Open a database connection and transaction. Return a storm.store.Store
    instance connected to the configured IVLE database.
    """
    return Store(create_database(get_conn_string()))

# USERS #

class User(Storm):
    """
    Represents an IVLE user.
    """
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
        return self.fullname

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
                Desc(Semester.semester),
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
        '''Return Projects that the user can submit.

        This will include projects for offerings in which the user is
        enrolled, as long as the project is not in a project set which has
        groups (ie. if maximum number of group members is 0).

        Unless active_only is False, only projects for active offerings will
        be returned.

        If an offering is specified, returned projects will be limited to
        those for that offering.
        '''
        return Store.of(self).find(Project,
            Project.project_set_id == ProjectSet.id,
            ProjectSet.max_students_per_group == 0,
            ProjectSet.offering_id == Offering.id,
            (offering is None) or (Offering.id == offering.id),
            Semester.id == Offering.semester_id,
            (not active_only) or (Semester.state == u'current'),
            Enrolment.offering_id == Offering.id,
            Enrolment.user_id == self.id)

    @staticmethod
    def hash_password(password):
        return md5.md5(password).hexdigest()

    @classmethod
    def get_by_login(cls, store, login):
        """
        Get the User from the db associated with a given store and
        login.
        """
        return store.find(cls, cls.login == unicode(login)).one()

    def get_permissions(self, user):
        if user and user.admin or user is self:
            return set(['view', 'edit', 'submit_project'])
        else:
            return set()

# SUBJECTS AND ENROLMENTS #

class Subject(Storm):
    __storm_table__ = "subject"

    id = Int(primary=True, name="subjectid")
    code = Unicode(name="subj_code")
    name = Unicode(name="subj_name")
    short_name = Unicode(name="subj_short_name")
    url = Unicode()

    offerings = ReferenceSet(id, 'Offering.subject_id')

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s '%s'>" % (type(self).__name__, self.short_name)

    def get_permissions(self, user):
        perms = set()
        if user is not None:
            perms.add('view')
            if user.admin:
                perms.add('edit')
        return perms

class Semester(Storm):
    __storm_table__ = "semester"

    id = Int(primary=True, name="semesterid")
    year = Unicode()
    semester = Unicode()
    state = Unicode()

    offerings = ReferenceSet(id, 'Offering.semester_id')
    enrolments = ReferenceSet(id,
                              'Offering.semester_id',
                              'Offering.id',
                              'Enrolment.offering_id')

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s/%s>" % (type(self).__name__, self.year, self.semester)

class Offering(Storm):
    __storm_table__ = "offering"

    id = Int(primary=True, name="offeringid")
    subject_id = Int(name="subject")
    subject = Reference(subject_id, Subject.id)
    semester_id = Int(name="semesterid")
    semester = Reference(semester_id, Semester.id)
    groups_student_permissions = Unicode()

    enrolments = ReferenceSet(id, 'Enrolment.offering_id')
    members = ReferenceSet(id,
                           'Enrolment.offering_id',
                           'Enrolment.user_id',
                           'User.id')
    project_sets = ReferenceSet(id, 'ProjectSet.offering_id')

    worksheets = ReferenceSet(id, 
        'Worksheet.offering_id', 
        order_by="seq_no"
    )

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %r in %r>" % (type(self).__name__, self.subject,
                                  self.semester)

    def enrol(self, user, role=u'student'):
        '''Enrol a user in this offering.'''
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

    def get_permissions(self, user):
        perms = set()
        if user is not None:
            enrolment = self.get_enrolment(user)
            if enrolment or user.admin:
                perms.add('view')
            if (enrolment and enrolment.role in (u'tutor', u'lecturer')) \
               or user.admin:
                perms.add('edit')
        return perms

    def get_enrolment(self, user):
        try:
            enrolment = self.enrolments.find(user=user).one()
        except NotOneError:
            enrolment = None

        return enrolment

class Enrolment(Storm):
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

# PROJECTS #

class ProjectSet(Storm):
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

class Project(Storm):
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

    def can_submit(self, principal):
        return (self in principal.get_projects() and
                self.deadline > datetime.datetime.now())

    def submit(self, principal, path, revision):
        if not self.can_submit(principal):
            raise Exception('cannot submit')

        a = Assessed.get(Store.of(self), principal, self)
        ps = ProjectSubmission()
        ps.path = path
        ps.revision = revision
        ps.date_submitted = datetime.datetime.now()
        ps.assessed = a

        return ps


class ProjectGroup(Storm):
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
        return '%s (%s)' % (self.nick, self.name)

    def get_projects(self, offering=None, active_only=True):
        '''Return Projects that the group can submit.

        This will include projects in the project set which owns this group,
        unless the project set disallows groups (in which case none will be
        returned).

        Unless active_only is False, projects will only be returned if the
        group's offering is active.

        If an offering is specified, projects will only be returned if it
        matches the group's.
        '''
        return Store.of(self).find(Project,
            Project.project_set_id == ProjectSet.id,
            ProjectSet.id == self.project_set.id,
            ProjectSet.max_students_per_group > 0,
            ProjectSet.offering_id == Offering.id,
            (offering is None) or (Offering.id == offering.id),
            Semester.id == Offering.semester_id,
            (not active_only) or (Semester.state == u'current'))


    def get_permissions(self, user):
        if user.admin or user in self.members:
            return set(['submit_project'])
        else:
            return set()

class ProjectGroupMembership(Storm):
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
    __storm_table__ = "assessed"

    id = Int(name="assessedid", primary=True)
    user_id = Int(name="loginid")
    user = Reference(user_id, User.id)
    project_group_id = Int(name="groupid")
    project_group = Reference(project_group_id, ProjectGroup.id)

    project_id = Int(name="projectid")
    project = Reference(project_id, Project.id)

    extensions = ReferenceSet(id, 'ProjectExtension.assessed_id')
    submissions = ReferenceSet(id, 'ProjectSubmission.assessed_id')

    def __repr__(self):
        return "<%s %r in %r>" % (type(self).__name__,
            self.user or self.project_group, self.project)

    @classmethod
    def get(cls, store, principal, project):
        t = type(principal)
        if t not in (User, ProjectGroup):
            raise AssertionError('principal must be User or ProjectGroup')

        a = store.find(cls,
            (t is User) or (cls.project_group_id == principal.id),
            (t is ProjectGroup) or (cls.user_id == principal.id),
            Project.id == project.id).one()

        if a is None:
            a = cls()
            if t is User:
                a.user = principal
            else:
                a.project_group = principal
            a.project = project
            store.add(a)

        return a


class ProjectExtension(Storm):
    __storm_table__ = "project_extension"

    id = Int(name="extensionid", primary=True)
    assessed_id = Int(name="assessedid")
    assessed = Reference(assessed_id, Assessed.id)
    deadline = DateTime()
    approver_id = Int(name="approver")
    approver = Reference(approver_id, User.id)
    notes = Unicode()

class ProjectSubmission(Storm):
    __storm_table__ = "project_submission"

    id = Int(name="submissionid", primary=True)
    assessed_id = Int(name="assessedid")
    assessed = Reference(assessed_id, Assessed.id)
    path = Unicode()
    revision = Int()
    date_submitted = DateTime()


# WORKSHEETS AND EXERCISES #

class Exercise(Storm):
    __storm_table__ = "exercise"
    id = Unicode(primary=True, name="identifier")
    name = Unicode()
    description = Unicode()
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

    def get_permissions(self, user):
        perms = set()
        roles = set()
        if user is not None:
            if user.admin:
                perms.add('edit')
                perms.add('view')
            elif u'lecturer' in set((e.role for e in user.active_enrolments)):
                perms.add('edit')
                perms.add('view')
            elif u'tutor' in set((e.role for e in user.active_enrolments)):
                perms.add('edit')
                perms.add('view')
            
        return perms
    
    def get_description(self):
        return rst(self.description)

    def delete(self):
        """Deletes the exercise, providing it has no associated worksheets."""
        if (self.worksheet_exercises.count() > 0):
            raise IntegrityError()
        for suite in self.test_suites:
            suite.delete()
        Store.of(self).remove(self)

class Worksheet(Storm):
    __storm_table__ = "worksheet"

    id = Int(primary=True, name="worksheetid")
    offering_id = Int(name="offeringid")
    identifier = Unicode()
    name = Unicode()
    assessable = Bool()
    data = Unicode()
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

    # XXX Refactor this - make it an instance method of Subject rather than a
    # class method of Worksheet. Can't do that now because Subject isn't
    # linked referentially to the Worksheet.
    @classmethod
    def get_by_name(cls, store, subjectname, worksheetname):
        """
        Get the Worksheet from the db associated with a given store, subject
        name and worksheet name.
        """
        return store.find(cls, cls.subject == unicode(subjectname),
            cls.name == unicode(worksheetname)).one()

    def remove_all_exercises(self):
        """
        Remove all exercises from this worksheet.
        This does not delete the exercises themselves. It just removes them
        from the worksheet.
        """
        store = Store.of(self)
        for ws_ex in self.all_worksheet_exercises:
            if ws_ex.saves.count() > 0 or ws_ex.attempts.count() > 0:
                raise IntegrityError()
        store.find(WorksheetExercise,
            WorksheetExercise.worksheet == self).remove()
            
    def get_permissions(self, user):
        return self.offering.get_permissions(user)
    
    def get_xml(self):
        """Returns the xml of this worksheet, converts from rst if required."""
        if self.format == u'rst':
            ws_xml = rst(self.data)
            return ws_xml
        else:
            return self.data
    
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

    def get_permissions(self, user):
        return self.worksheet.get_permissions(user)
    

class ExerciseSave(Storm):
    """
    Represents a potential solution to an exercise that a user has submitted
    to the server for storage.
    A basic ExerciseSave is just the current saved text for this exercise for
    this user (doesn't count towards their attempts).
    ExerciseSave may be extended with additional semantics (such as
    ExerciseAttempt).
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
            self.exercise.name, self.user.login, self.date.strftime("%c"))

class ExerciseAttempt(ExerciseSave):
    """
    An ExerciseAttempt is a special case of an ExerciseSave. Like an
    ExerciseSave, it constitutes exercise solution data that the user has
    submitted to the server for storage.
    In addition, it contains additional information about the submission.
    complete - True if this submission was successful, rendering this exercise
        complete for this user.
    active - True if this submission is "active" (usually true). Submissions
        may be de-activated by privileged users for special reasons, and then
        they won't count (either as a penalty or success), but will still be
        stored.
    """
    __storm_table__ = "exercise_attempt"
    __storm_primary__ = "ws_ex_id", "user_id", "date"

    # The "text" field is the same but has a different name in the DB table
    # for some reason.
    text = Unicode(name="attempt")
    complete = Bool()
    active = Bool()
    
    def get_permissions(self, user):
        return set(['view']) if user is self.user else set()
  
class TestSuite(Storm):
    """A Testsuite acts as a container for the test cases of an exercise."""
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
        for vaariable in self.variables:
            variable.delete()
        for test_case in self.test_cases:
            test_case.delete()
        Store.of(self).remove(self)

class TestCase(Storm):
    """A TestCase is a member of a TestSuite.
    
    It contains the data necessary to check if an exercise is correct"""
    __storm_table__ = "test_case"
    __storm_primary__ = "testid", "suiteid"
    
    testid = Int()
    suiteid = Int()
    suite = Reference(suiteid, "TestSuite.suiteid")
    passmsg = Unicode()
    failmsg = Unicode()
    test_default = Unicode()
    seq_no = Int()
    
    parts = ReferenceSet(testid, "TestCasePart.testid")
    
    __init__ = _kwarg_init
    
    def delete(self):
        for part in self.parts:
            part.delete()
        Store.of(self).remove(self)

class TestSuiteVar(Storm):
    """A container for the arguments of a Test Suite"""
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
    """A container for the test elements of a Test Case"""
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
