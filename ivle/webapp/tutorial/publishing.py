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

import datetime

from storm.locals import Store

from ivle.database import (Exercise, ExerciseAttempt, Offering, User,
                           Worksheet, WorksheetExercise)

from ivle.webapp import ApplicationRoot
from ivle.webapp.publisher import ROOT
from ivle.webapp.publisher.decorators import forward_route, reverse_route

import ivle.worksheet

from ivle.webapp.tutorial.service import TIMESTAMP_FORMAT

# If True, getattempts or getattempt will allow browsing of inactive/disabled
# attempts. If False, will not allow this.
HISTORY_ALLOW_INACTIVE = False

@forward_route(ApplicationRoot, '+exercises', argc=1)
def root_to_exercise(root, exercise_name):
    return root.store.find(
        Exercise,
        Exercise.id == exercise_name
        ).one()

@reverse_route(Exercise)
def exercise_url(exercise):
    return (ROOT, ('+exercises', exercise.id))


@forward_route(Offering, '+worksheets', argc=1)
def offering_to_worksheet(offering, worksheet_name):
    return Store.of(offering).find(
        Worksheet,
        Worksheet.offering == offering,
        Worksheet.identifier == worksheet_name
        ).one()

@reverse_route(Worksheet)
def worksheet_url(worksheet):
    return (worksheet.offering, ('+worksheets', worksheet.identifier))


@forward_route(Worksheet, argc=1)
def worksheet_to_worksheetexercise(worksheet, exercise_name):
    return Store.of(worksheet).find(
        WorksheetExercise,
        WorksheetExercise.exercise_id == exercise_name,
        WorksheetExercise.worksheet == worksheet
        ).one()

@reverse_route(WorksheetExercise)
def worksheetexercise_url(worksheetexercise):
    return (worksheetexercise.worksheet,
            worksheetexercise.exercise.identifier)


class ExerciseAttempts(object):
    """The set of exercise attempts for a user and exercise.

    A combination of a User and WorksheetExercise, this provides access to
    the User's ExerciseAttempts.
    """

    def __init__(self, worksheet_exercise, user):
        self.worksheet_exercise = worksheet_exercise
        self.user = user

    def get_permissions(self, user, config):
        return self.user.get_permissions(user, config)


@forward_route(WorksheetExercise, '+attempts', argc=1)
def worksheetexercise_to_exerciseattempts(worksheet_exercise, login):
    user = User.get_by_login(Store.of(worksheet_exercise), login)
    if user is None:
        return None
    return ExerciseAttempts(worksheet_exercise, user)

@reverse_route(ExerciseAttempts)
def exerciseattempts_url(exerciseattempts):
    return (exerciseattempts.worksheet_exercise,
            ('+attempts', exerciseattempts.user.login))


@forward_route(ExerciseAttempts, argc=1)
def exerciseattempts_to_attempt(exercise_attempts, date):
    try:
        date = datetime.datetime.strptime(date, TIMESTAMP_FORMAT)
    except ValueError:
        return None

    # XXX Hack around Google Code issue #87
    # Query from the given date +1 secnod.
    # Date is in seconds (eg. 3:47:12), while the data is in finer time
    # (eg. 3:47:12.3625). The query "date <= 3:47:12" will fail because
    # 3:47:12.3625 is greater. Hence we do the query from +1 second,
    # "date <= 3:47:13", and it finds the correct submission, UNLESS there
    # are multiple submissions inside the same second.
    date += datetime.timedelta(seconds=1)

    return ivle.worksheet.utils.get_exercise_attempt(
                Store.of(exercise_attempts.user),
                exercise_attempts.user, exercise_attempts.worksheet_exercise,
                as_of=date, allow_inactive=HISTORY_ALLOW_INACTIVE)

@reverse_route(ExerciseAttempt)
def exerciseattempt_url(exerciseattempt):
    return (ExerciseAttempts(exerciseattempt.worksheet_exercise,
                             exerciseattempt.user),
            exerciseattempt.date.strftime(TIMESTAMP_FORMAT)
            )
