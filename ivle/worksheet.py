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

def get_exercise_status(store, user, exercise):
    """Given a storm.store, User and Exercise, returns information about
    the user's performance on that problem.
    Returns a tuple of:
        - A boolean, whether they have successfully passed this exercise.
        - An int, the number of attempts they have made up to and
          including the first successful attempt (or the total number of
          attempts, if not yet successful).
    """
    ExerciseAttempt = ivle.database.ExerciseAttempt
    # A Storm expression denoting all active attempts by this user for this
    # exercise.
    is_relevant = ((ExerciseAttempt.user_id == user.id) &
                   (ExerciseAttempt.exercise_id == exercise.id) &
                   (ExerciseAttempt.active == True))

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

def get_exercise_stored_text(store, user, exercise):
    """Given a storm.store, User and Exercise, returns the text of the last
    saved/submitted attempt for this question, as an
    ivle.database.ExerciseSave object (note that ExerciseAttempt is a subclass
    of ExerciseSave).
    Returns None if the user has not saved or made an attempt on this
    problem.
    If the user has both saved and submitted, it returns whichever was
    made last.
    """
    ExerciseSave = ivle.database.ExerciseSave
    ExerciseAttempt = ivle.database.ExerciseAttempt

    # Get the saved text, or None
    saved = store.find(ExerciseSave,
                ExerciseSave.user_id == user.id,
                ExerciseSave.exercise_id == exercise.id).one()

    # Get the most recent attempt, or None
    attempt = store.find(ExerciseAttempt,
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.exercise_id == exercise.id,
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
