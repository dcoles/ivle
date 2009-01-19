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
            'Exercise', 'Worksheet',
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

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %r in %r>" % (type(self).__name__, self.subject,
                                  self.semester)

class Enrolment(Storm):
    __storm_table__ = "enrolment"
    __storm_primary__ = "user_id", "offering_id"

    user_id = Int(name="loginid")
    user = Reference(user_id, User.id)
    offering_id = Int(name="offeringid")
    offering = Reference(offering_id, Offering.id)
    notes = Unicode()
    active = Bool()

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

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s in %r>" % (type(self).__name__, self.name,
                                  self.project_set.offering)

    @property
    def members(self):
        return Store.of(self).find(User,
            ProjectGroupMembership.project_group_id == self.id,
            User.id == ProjectGroupMembership.user_id)

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

    id = Int(primary=True, name="problemid")
    name = Unicode(name="identifier")
    spec = Unicode()

    worksheets = ReferenceSet(id,
        'WorksheetExercise.exercise_id',
        'WorksheetExercise.worksheet_id',
        'Worksheet.id'
    )

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, self.name)

    @classmethod
    def get_by_name(cls, store, name):
        """
        Get the Exercise from the db associated with a given store and name.
        If the exercise is not in the database, creates it and inserts it
        automatically.
        """
        ex = store.find(cls, cls.name == unicode(name)).one()
        if ex is not None:
            return ex
        ex = Exercise(name=unicode(name))
        store.add(ex)
        store.commit()
        return ex

class Worksheet(Storm):
    __storm_table__ = "worksheet"

    id = Int(primary=True, name="worksheetid")
    # XXX subject is not linked to a Subject object. This is a property of
    # the database, and will be refactored.
    subject = Unicode()
    name = Unicode(name="identifier")
    assessable = Bool()
    mtime = DateTime()

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

class WorksheetExercise(Storm):
    __storm_table__ = "worksheet_problem"
    __storm_primary__ = "worksheet_id", "exercise_id"

    worksheet_id = Int(name="worksheetid")
    worksheet = Reference(worksheet_id, Worksheet.id)
    exercise_id = Int(name="problemid")
    exercise = Reference(exercise_id, Exercise.id)
    optional = Bool()

    __init__ = _kwarg_init

    def __repr__(self):
        return "<%s %s in %s>" % (type(self).__name__, self.exercise.name,
                                  self.worksheet.name)
