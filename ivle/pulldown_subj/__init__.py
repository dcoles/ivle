# IVLE - Informatics Virtual Learning Environment
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

# Module: Subject Pulldown
# Author: Matt Giuca
# Date:   7/7/2008

# Pluggable subject pulldown module.
# Grabs a student's subject list from a source specified in conf.py.

# Each module should have a get_subjects(login) function, which takes login
# and returns a list of (subject, semester) pairs (both strings), or None
# if the user can't be found. May also raise a SubjectError which is fatal.

import os
import sys
import datetime

from subjecterror import SubjectError
import ivle.conf

from ivle.database import Subject, Offering, Semester, AlreadyEnrolledError

def get_subjects(login):
    """
    Looks up the student in whatever modules are available, using login.
    If successful, returns a list of (subject, semester) pairs (both strings).
    Raises a SubjectError if unsuccessful.
    """
    for modname, m in subj_modules:
        result = m(login)
        if result is not None:
            return result
    return []

def enrol_user(store, user, year=None):
    """
    Looks up the student in whatever modules are available.
    The pulldown does not tell us what year to enrol the student for, so the
    year may be specified (as a string). If unspecified, will enrol in the
    current year according to the system clock.
    If successful, enrols the student (in the database) in all subjects in the
    system. Subjects which the pulldown tells us the student is in, but which
    are not in the system are ignored.
    Does not unenrol the student from any subjects.
    Does not complain if the student is already enrolled in any subjects.
    Raises a SubjectError if the pulldown module says so.

    Returns the number of subjects the user was enrolled in (not including
    subjects outside the system, or subjects already enrolled).
    """
    if year is None:
        year = unicode(datetime.datetime.now().year)

    count = 0
    for subject, semester in get_subjects(user.login):
        offering = store.find(Offering,
                              Subject.code == subject,
                              Offering.subject_id == Subject.id,
                              Semester.year == year,
                              Semester.semester == semester,
                              Offering.semester_id == Semester.id).one()

        # We can't find a matching offering, so we don't care about it.
        if not offering:
            continue

        try:
            offering.enrol(user)
            count += 1
        except AlreadyEnrolledError:
            pass
    return count

# Allow imports to get files from this directory.
# Get the directory that this module (authenticate) is in
plugpath = os.path.split(sys.modules[__name__].__file__)[0]
# Add it to sys.path
sys.path.append(plugpath)

# Create a global variable "subj_modules", a list of (name, function object)s.
# This list consists of null_subj, plus the "get_subject" functions of all the
# plugin subject pulldown modules.

subj_modules = []
for modname in ivle.conf.subject_pulldown_modules.split(','):
    try:
        mod = __import__(modname)
    except ImportError:
        raise SubjectError("Internal error: "
            "Can't import subject pulldown module %s"
            % repr(modname))
    except ValueError:
        # If auth_modules is "", we may get an empty string - ignore
        continue
    try:
        subjfunc = mod.get_subjects
    except AttributeError:
        raise SubjectError("Internal error: Subject pulldown module %r has no "
            "'get_subjects' function" % modname)
    subj_modules.append((modname, subjfunc))
