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

# Author: Matt Giuca

"""
Worksheet Utility Functions

This module provides functions for tutorial and worksheet computations.
"""

from storm.locals import And, Asc, Desc
import ivle.database
from ivle.database import ExerciseAttempt, ExerciseSave, Worksheet

__all__ = ['get_exercise_status', 'get_exercise_stored_text',
           'get_exercise_attempts', 'get_exercise_attempt',
          ]

def get_exercise_status(store, user, exercise, worksheet):
    """Given a storm.store, User and Exercise, returns information about
    the user's performance on that problem.
    Returns a tuple of:
        - A boolean, whether they have successfully passed this exercise.
        - An int, the number of attempts they have made up to and
          including the first successful attempt (or the total number of
          attempts, if not yet successful).
    """
    # A Storm expression denoting all active attempts by this user for this
    # exercise.
    is_relevant = ((ExerciseAttempt.user_id == user.id) &
                   (ExerciseAttempt.exercise_id == exercise.id) &
                   (ExerciseAttempt.active == True) &
                   (ExerciseAttempt.worksheetid == worksheet.id))

    # Get the first successful active attempt, or None if no success yet.
    # (For this user, for this exercise).
    first_success = store.find(ExerciseAttempt, is_relevant,
            ExerciseAttempt.complete == True
        ).order_by(Asc(ExerciseAttempt.date)).first()

    if first_success is not None:
        # Get the total number of active attempts up to and including the
        # first successful attempt.
        # (Subsequent attempts don't count, because the user had already
        # succeeded by then).
        num_attempts = store.find(ExerciseAttempt, is_relevant,
                ExerciseAttempt.date <= first_success.date).count()
    else:
        # User has not yet succeeded.
        # Get the total number of active attempts.
        num_attempts = store.find(ExerciseAttempt, is_relevant).count()

    return first_success is not None, num_attempts

def get_exercise_stored_text(store, user, exercise, worksheet):
    """Given a storm.store, User and Exercise, returns an
    ivle.database.ExerciseSave object for the last saved/submitted attempt for
    this question (note that ExerciseAttempt is a subclass of ExerciseSave).
    Returns None if the user has not saved or made an attempt on this
    problem.
    If the user has both saved and submitted, it returns whichever was
    made last.
    """

    # Get the saved text, or None
    saved = store.find(ExerciseSave,
                ExerciseSave.user_id == user.id,
                ExerciseSave.exercise_id == exercise.id,
                ExerciseSave.worksheetid == worksheet.id).one()

    # Get the most recent attempt, or None
    attempt = store.find(ExerciseAttempt,
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.exercise_id == exercise.id,
            ExerciseAttempt.worksheetid == worksheet.id,
            ExerciseAttempt.active == True,
        ).order_by(Asc(ExerciseAttempt.date)).last()

    # Pick the most recent of these two
    if saved is not None:
        if attempt is not None:
            return saved if saved.date > attempt.date else attempt
        else:
            return saved
    else:
        if attempt is not None:
            return attempt
        else:
            return None

def _get_exercise_attempts(store, user, exercise, worksheet, as_of=None,
        allow_inactive=False):
    """Same as get_exercise_attempts, but doesn't convert Storm's iterator
    into a list."""

    # Get the most recent attempt before as_of, or None
    return store.find(ExerciseAttempt,
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.exercise_id == exercise.id,
            ExerciseAttempt.worksheetid == worksheet.id,
            True if allow_inactive else ExerciseAttempt.active == True,
            True if as_of is None else ExerciseAttempt.date <= as_of,
        ).order_by(Desc(ExerciseAttempt.date))

def get_exercise_attempts(store, user, exercise, worksheet, as_of=None,
        allow_inactive=False):
    """Given a storm.store, User and Exercise, returns a list of
    ivle.database.ExerciseAttempt objects, one for each attempt made for the
    exercise, sorted from latest to earliest.

    as_of: Optional datetime.datetime object. If supplied, only returns
        attempts made before or at this time.
    allow_inactive: If True, will return disabled attempts.
    """
    return list(_get_exercise_attempts(store, user, exercise, worksheet, as_of,
        allow_inactive))

def get_exercise_attempt(store, user, exercise, worksheet, as_of=None,
        allow_inactive=False):
    """Given a storm.store, User and Exercise, returns an
    ivle.database.ExerciseAttempt object for the last submitted attempt for
    this question.
    Returns None if the user has not made an attempt on this
    problem.

    as_of: Optional datetime.datetime object. If supplied, only returns
        attempts made before or at this time.
    allow_inactive: If True, will return disabled attempts.
    """
    return _get_exercise_attempts(store, user, exercise, worksheet, as_of,
        allow_inactive).first()

def save_exercise(store, user, exercise, worksheet, text, date):
    """Save an exercise for a user.

    Given a store, User, Exercise and text and date, save the text to the
    database. This will create the ExerciseSave if needed.
    """
    saved = store.find(ivle.database.ExerciseSave,
                ivle.database.ExerciseSave.user_id == user.id,
                ivle.database.ExerciseSave.exercise_id == exercise.id,
                ivle.database.ExerciseSave.worksheetid == worksheet.id
                ).one()
    if saved is None:
        saved = ivle.database.ExerciseSave(user=user, exercise=exercise, 
                                           worksheet=worksheet)
        store.add(saved)

    saved.date = date
    saved.text = text

def calculate_score(store, user, worksheet):
    """
    Given a storm.store, User, Exercise and Worksheet, calculates a score for
    the user on the given worksheet.
    Returns a 4-tuple of ints, consisting of:
    (No. mandatory exercises completed,
     Total no. mandatory exercises,
     No. optional exercises completed,
     Total no. optional exercises)
    """
    mand_done = 0
    mand_total = 0
    opt_done = 0
    opt_total = 0

    # Get the student's pass/fail for each exercise in this worksheet
    for worksheet_exercise in worksheet.worksheet_exercises:
        exercise = worksheet_exercise.exercise
        optional = worksheet_exercise.optional

        done, _ = get_exercise_status(store, user, exercise)
        # done is a bool, whether this student has completed that problem
        if optional:
            opt_total += 1
            if done: opt_done += 1
        else:
            mand_total += 1
            if done: mand_done += 1

    return mand_done, mand_total, opt_done, opt_total
