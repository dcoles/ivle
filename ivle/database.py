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

import ivle.conf
import ivle.caps

__all__ = ['get_store',
            'User',
            'Subject', 'Semester', 'Offering', 'Enrolment',
            'ProjectSet', 'Project', 'ProjectGroup', 'ProjectGroupMembership',
            'Exercise', 'Worksheet', 'WorksheetExercise',
            'ExerciseSave', 'ExerciseAttempt',
            'AlreadyEnrolledError', 'TestCase', 'TestSuite', 'TestSuiteVar'
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
    return "postgres://%s:%s@%s:%d/%s" % (ivle.conf.db_user,
        ivle.conf.db_password, ivle.conf.db_host, ivle.conf.db_port,
        ivle.conf.db_dbname)

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
    rolenm = Unicode()
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

    def _get_role(self):
        if self.rolenm is None:
            return None
        return ivle.caps.Role(self.rolenm)
    def _set_role(self, value):
        if not isinstance(value, ivle.caps.Role):
            raise TypeError("role must be an ivle.caps.Role")
        self.rolenm = unicode(value)
    role = property(_get_role, _set_role)

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

    def hasCap(self, capability):
        """Given a capability (which is a Role object), returns True if this
        User has that capability, False otherwise.
        """
        return self.role.hasCap(capability)

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
        if user and user.rolenm == 'admin' or user is self:
            return set(['view', 'edit'])
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
            if user.rolenm == 'admin':
                perms.add('edit')
        return perms

class Semester(Storm):
    __storm_table__ = "semester"

    id = Int(primary=True, name="semesterid")
    year = Unicode()
    semester = Unicode()
    active = Bool()

    offerings = ReferenceSet(id, 'Offering.semester_id')

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

    worksheets = ReferenceSet(id, 'Worksheet.offering_id')

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %r in %r>" % (type(self).__name__, self.subject,
                                  self.semester)

    def enrol(self, user):
        '''Enrol a user in this offering.'''
        # We'll get a horrible database constraint violation error if we try
        # to add a second enrolment.
        if Store.of(self).find(Enrolment,
                               Enrolment.user_id == user.id,
                               Enrolment.offering_id == self.id).count() == 1:
            raise AlreadyEnrolledError()

        e = Enrolment(user=user, offering=self, active=True)
        self.enrolments.add(e)

    def get_permissions(self, user):
        perms = set()
        if user is not None:
            perms.add('view')
            if user.rolenm == 'admin':
                perms.add('edit')
        return perms

class Enrolment(Storm):
    __storm_table__ = "enrolment"
    __storm_primary__ = "user_id", "offering_id"

    user_id = Int(name="loginid")
    user = Reference(user_id, User.id)
    offering_id = Int(name="offeringid")
    offering = Reference(offering_id, Offering.id)
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

class AlreadyEnrolledError(Exception):
    pass

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
    synopsis = Unicode()
    url = Unicode()
    project_set_id = Int(name="projectsetid")
    project_set = Reference(project_set_id, ProjectSet.id)
    deadline = DateTime()

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s '%s' in %r>" % (type(self).__name__, self.synopsis,
                                  self.project_set.offering)

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

# WORKSHEETS AND EXERCISES #

class Exercise(Storm):
    # Note: Table "problem" is called "Exercise" in the Object layer, since
    # it's called that everywhere else.
    __storm_table__ = "problem"
#TODO: Add in a field for the user-friendly identifier
    id = Unicode(primary=True, name="identifier")
    name = Unicode()
    description = Unicode()
    partial = Unicode()
    solution = Unicode()
    include = Unicode()
    num_rows = Int()

    worksheets = ReferenceSet(id,
        'WorksheetExercise.exercise_id',
        'WorksheetExercise.worksheet_id',
        'Worksheet.id'
    )
    
    test_suites = ReferenceSet(id, 'TestSuite.exercise_id')

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self.name)

#    @classmethod
#    def get_by_name(cls, store, name):
#        """
#        Get the Exercise from the db associated with a given store and name.
#        If the exercise is not in the database, creates it and inserts it
#        automatically.
#        """
#        ex = store.find(cls, cls.name == unicode(name)).one()
#        if ex is not None:
#            return ex
#        ex = Exercise(name=unicode(name))
#        store.add(ex)
#        store.commit()
#        return ex

class Worksheet(Storm):
    __storm_table__ = "worksheet"

    id = Int(primary=True, name="worksheetid")
    # XXX subject is not linked to a Subject object. This is a property of
    # the database, and will be refactored.
    subject = Unicode()
    offering_id = Int(name="offeringid")
    name = Unicode(name="identifier")
    assessable = Bool()
    mtime = DateTime()

    attempts = ReferenceSet(id, "ExerciseAttempt.worksheetid")
    offering = Reference(offering_id, 'Offering.id')

    exercises = ReferenceSet(id,
        'WorksheetExercise.worksheet_id',
        'WorksheetExercise.exercise_id',
        Exercise.id)
    # Use worksheet_exercises to get access to the WorksheetExercise objects
    # binding worksheets to exercises. This is required to access the
    # "optional" field.
    worksheet_exercises = ReferenceSet(id,
        'WorksheetExercise.worksheet_id')
        

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

    def remove_all_exercises(self, store):
        """
        Remove all exercises from this worksheet.
        This does not delete the exercises themselves. It just removes them
        from the worksheet.
        """
        store.find(WorksheetExercise,
            WorksheetExercise.worksheet == self).remove()
            
    def get_permissions(self, user):
        return self.offering.get_permissions(user)

class WorksheetExercise(Storm):
    __storm_table__ = "worksheet_problem"
    __storm_primary__ = "worksheet_id", "exercise_id"

    worksheet_id = Int(name="worksheetid")
    worksheet = Reference(worksheet_id, Worksheet.id)
    exercise_id = Unicode(name="problemid")
    exercise = Reference(exercise_id, Exercise.id)
    optional = Bool()

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s in %s>" % (type(self).__name__, self.exercise.name,
                                  self.worksheet.name)

class ExerciseSave(Storm):
    """
    Represents a potential solution to an exercise that a user has submitted
    to the server for storage.
    A basic ExerciseSave is just the current saved text for this exercise for
    this user (doesn't count towards their attempts).
    ExerciseSave may be extended with additional semantics (such as
    ExerciseAttempt).
    """
    __storm_table__ = "problem_save"
    __storm_primary__ = "exercise_id", "user_id", "date"

    exercise_id = Unicode(name="problemid")
    exercise = Reference(exercise_id, Exercise.id)
    user_id = Int(name="loginid")
    user = Reference(user_id, User.id)
    date = DateTime()
    text = Unicode()
    worksheetid = Int()
    worksheet = Reference(worksheetid, Worksheet.id)

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
    __storm_table__ = "problem_attempt"
    __storm_primary__ = "exercise_id", "user_id", "date"

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
    exercise_id = Unicode(name="problemid")
    description = Unicode()
    seq_no = Int()
    function = Unicode()
    stdin = Unicode()
    exercise = Reference(exercise_id, Exercise.id)
    test_cases = ReferenceSet(suiteid, 'TestCase.suiteid')
    variables = ReferenceSet(suiteid, 'TestSuiteVar.suiteid')

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

class TestSuiteVar(Storm):
    """A container for the arguments of a Test Suite"""
    __storm_table__ = "suite_variables"
    __storm_primary__ = "varid"
    
    varid = Int()
    suiteid = Int()
    var_name = Unicode()
    var_value = Unicode()
    var_type = Unicode()
    arg_no = Int()
    
    suite = Reference(suiteid, "TestSuite.suiteid")
    
    __init__ = _kwarg_init
    
class TestCasePart(Storm):
    """A container for the test elements of a Test Case"""
    __storm_table__ = "test_case_parts"
    __storm_primary__ = "partid"
    
    partid = Int()
    testid = Int()
    
    part_type = Unicode()
    test_type = Unicode()
    data = Unicode()
    filename = Unicode()
    
    test = Reference(testid, "TestCase.testid")
    
    __init__ = _kwarg_init
