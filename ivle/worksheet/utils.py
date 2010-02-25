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

import os.path

from storm.locals import And, Asc, Desc, Store
import genshi

import ivle.database
from ivle.database import ExerciseAttempt, ExerciseSave, Worksheet, \
                          WorksheetExercise, Exercise, User
import ivle.webapp.tutorial.test

__all__ = ['ExerciseNotFound', 'get_exercise_status',
           'get_exercise_statistics',
           'get_exercise_stored_text', 'get_exercise_attempts',
           'get_exercise_attempt', 'test_exercise_submission',
          ]

class ExerciseNotFound(Exception):
    pass

def get_exercise_status(store, user, worksheet_exercise, as_of=None):
    """Given a storm.store, User and Exercise, returns information about
    the user's performance on that problem.
    @param store: A storm.store
    @param user: A User.
    @param worksheet_exercise: An Exercise.
    @param as_of: Optional datetime. If supplied, gets the status as of as_of.
    Returns a tuple of:
        - A boolean, whether they have successfully passed this exercise.
        - An int, the number of attempts they have made up to and
          including the first successful attempt (or the total number of
          attempts, if not yet successful).
    """
    # A Storm expression denoting all active attempts by this user for this
    # exercise.
    is_relevant = ((ExerciseAttempt.user_id == user.id) &
            (ExerciseAttempt.ws_ex_id == worksheet_exercise.id) &
            (ExerciseAttempt.active == True))
    if as_of is not None:
        is_relevant &= ExerciseAttempt.date <= as_of

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

def get_exercise_statistics(store, worksheet_exercise):
    """Return statistics about an exercise (with respect to a given
    worksheet).
    (number of students completed, number of students attempted)."""
    # Count the set of Users whose ID matches an attempt in this worksheet
    num_completed = store.find(User, User.id == ExerciseAttempt.user_id,
        ExerciseAttempt.ws_ex_id == worksheet_exercise.id,
        ExerciseAttempt.complete == True).config(distinct=True).count()
    num_attempted = store.find(User, User.id == ExerciseAttempt.user_id,
        ExerciseAttempt.ws_ex_id == worksheet_exercise.id,
        ).config(distinct=True).count()
    return num_completed, num_attempted

def get_exercise_stored_text(store, user, worksheet_exercise):
    """Given a storm.store, User and WorksheetExercise, returns an
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
                ExerciseSave.ws_ex_id == worksheet_exercise.id).one()

    # Get the most recent attempt, or None
    attempt = store.find(ExerciseAttempt,
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.active == True,
            ExerciseAttempt.ws_ex_id == worksheet_exercise.id
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

def _get_exercise_attempts(store, user, worksheet_exercise, as_of=None,
        allow_inactive=False):
    """Same as get_exercise_attempts, but doesn't convert Storm's iterator
    into a list."""

    # Get the most recent attempt before as_of, or None
    return store.find(ExerciseAttempt,
            ExerciseAttempt.user_id == user.id,
            ExerciseAttempt.ws_ex_id == worksheet_exercise.id,
            True if allow_inactive else ExerciseAttempt.active == True,
            True if as_of is None else ExerciseAttempt.date <= as_of,
        ).order_by(Desc(ExerciseAttempt.date))

def get_exercise_attempts(store, user, worksheet_exercise, as_of=None,
        allow_inactive=False):
    """Given a storm.store, User and Exercise, returns a list of
    ivle.database.ExerciseAttempt objects, one for each attempt made for the
    exercise, sorted from latest to earliest.

    as_of: Optional datetime.datetime object. If supplied, only returns
        attempts made before or at this time.
    allow_inactive: If True, will return disabled attempts.
    """
    return list(_get_exercise_attempts(store, user, worksheet_exercise, as_of,
        allow_inactive))

def get_exercise_attempt(store, user, worksheet_exercise, as_of=None,
        allow_inactive=False):
    """Given a storm.store, User and WorksheetExercise, returns an
    ivle.database.ExerciseAttempt object for the last submitted attempt for
    this question.
    Returns None if the user has not made an attempt on this
    problem.

    as_of: Optional datetime.datetime object. If supplied, only returns
        attempts made before or at this time.
    allow_inactive: If True, will return disabled attempts.
    """
    return _get_exercise_attempts(store, user, worksheet_exercise, as_of,
        allow_inactive).first()

def save_exercise(store, user, worksheet_exercise, text, date):
    """Save an exercise for a user.

    Given a store, User, WorksheetExercise, text and date, save the text to the
    database. This will create the ExerciseSave if needed.
    """
    saved = store.find(ivle.database.ExerciseSave,
                ivle.database.ExerciseSave.user_id == user.id,
                ivle.database.ExerciseSave.ws_ex_id == worksheet_exercise.id
                ).one()
    if saved is None:
        saved = ivle.database.ExerciseSave(user=user, 
                                        worksheet_exercise=worksheet_exercise)
        store.add(saved)

    saved.date = date
    saved.text = text

def calculate_score(store, user, worksheet, as_of=None):
    """
    Given a storm.store, User, Exercise and Worksheet, calculates a score for
    the user on the given worksheet.
    @param store: A storm.store
    @param user: A User.
    @param worksheet: A Worksheet.
    @param as_of: Optional datetime. If supplied, gets the score as of as_of.
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
        worksheet = worksheet_exercise.worksheet
        optional = worksheet_exercise.optional

        done, _ = get_exercise_status(store, user, worksheet_exercise, as_of)
        # done is a bool, whether this student has completed that problem
        if optional:
            opt_total += 1
            if done: opt_done += 1
        else:
            mand_total += 1
            if done: mand_done += 1

    return mand_done, mand_total, opt_done, opt_total

def calculate_mark(mand_done, mand_total):
    """Calculate a subject mark, given the result of all worksheets.
    @param mand_done: The total number of mandatory exercises completed by
        some student, across all worksheets.
    @param mand_total: The total number of mandatory exercises across all
        worksheets in the offering.
    @return: (percent, mark, mark_total)
        percent: The percentage of exercises the student has completed, as an
            integer between 0 and 100 inclusive.
        mark: The mark the student has received, based on the percentage.
        mark_total: The total number of marks available (currently hard-coded
            as 5).
    """
    # We want to display a students mark out of 5. However, they are
    # allowed to skip 1 in 5 questions and still get 'full marks'.
    # Hence we divide by 16, essentially making 16 percent worth
    # 1 star, and 80 or above worth 5.
    if mand_total > 0:
        percent_int = (100 * mand_done) // mand_total
    else:
        # Avoid Div0, just give everyone 0 marks if there are none available
        percent_int = 0
    # percent / 16, rounded down, with a maximum mark of 5
    max_mark = 5
    mark = min(percent_int // 16, max_mark)
    return (percent_int, mark, max_mark)

def update_exerciselist(worksheet):
    """Runs through the worksheetstream, generating the appropriate
    WorksheetExercises, and de-activating the old ones."""
    exercises = []
    # Turns the worksheet into an xml stream, and then finds all the 
    # exercise nodes in the stream.
    worksheetdata = genshi.XML(worksheet.data_xhtml)
    for kind, data, pos in worksheetdata:
        if kind is genshi.core.START:
            # Data is a tuple of tag name and a list of name->value tuples
            if data[0] == 'exercise':
                src = ""
                optional = False
                for attr in data[1]:
                    if attr[0] == 'src':
                        src = attr[1]
                    if attr[0] == 'optional':
                        optional = attr[1] == 'true'
                if src != "":
                    exercises.append((src, optional))
    ex_num = 0
    # Set all current worksheet_exercises to be inactive
    db_worksheet_exercises = Store.of(worksheet).find(WorksheetExercise,
        WorksheetExercise.worksheet_id == worksheet.id)
    for worksheet_exercise in db_worksheet_exercises:
        worksheet_exercise.active = False
    
    for exerciseid, optional in exercises:
        worksheet_exercise = Store.of(worksheet).find(WorksheetExercise,
            WorksheetExercise.worksheet_id == worksheet.id,
            Exercise.id == WorksheetExercise.exercise_id,
            Exercise.id == exerciseid).one()
        if worksheet_exercise is None:
            exercise = Store.of(worksheet).find(Exercise,
                Exercise.id == exerciseid
            ).one()
            if exercise is None:
                raise ExerciseNotFound(exerciseid)
            worksheet_exercise = WorksheetExercise()
            worksheet_exercise.worksheet_id = worksheet.id
            worksheet_exercise.exercise_id = exercise.id
            Store.of(worksheet).add(worksheet_exercise)
        worksheet_exercise.active = True
        worksheet_exercise.seq_no = ex_num
        worksheet_exercise.optional = optional


def test_exercise_submission(config, user, exercise, code):
    """Test the given code against an exercise.

    The code is run in a console process as the provided user.
    """
    # Start a console to run the tests on
    jail_path = os.path.join(config['paths']['jails']['mounts'],
                             user.login)
    working_dir = os.path.join("/home", user.login)
    cons = ivle.console.Console(config, user.unixid, jail_path,
                                working_dir)

    # Parse the file into a exercise object using the test suite
    exercise_obj = ivle.webapp.tutorial.test.parse_exercise_file(
        exercise, cons)

    # Run the test cases. Get the result back as a JSONable object.
    # Return it.
    test_results = exercise_obj.run_tests(code)

    # Close the console
    cons.close()

    return test_results


class FakeWorksheetForMarks:
    """This class represents a worksheet and a particular students progress
    through it.
    
    Do not confuse this with a worksheet in the database. This worksheet
    has extra information for use in the output, such as marks."""
    def __init__(self, id, name, assessable, published):
        self.id = id
        self.name = name
        self.assessable = assessable
        self.published = published
        self.complete_class = ''
        self.optional_message = ''
        self.total = 0
        self.mand_done = 0
    def __repr__(self):
        return ("Worksheet(id=%s, name=%s, assessable=%s)"
                % (repr(self.id), repr(self.name), repr(self.assessable)))


# XXX: This really shouldn't be needed.
def create_list_of_fake_worksheets_and_stats(config, store, user, offering):
    """Take an offering's real worksheets, converting them into stats.

    The worksheet listing views expect special fake worksheet objects
    that contain counts of exercises, whether they've been completed,
    that sort of thing. A fake worksheet object is used to contain
    these values, because nobody has managed to refactor the need out
    yet.
    """
    new_worksheets = []
    problems_done = 0
    problems_total = 0

    # Offering.worksheets is ordered by the worksheets seq_no
    worksheets = offering.worksheets

    # Unless we can edit worksheets, hide unpublished ones.
    if 'edit_worksheets' not in offering.get_permissions(user, config):
        worksheets = worksheets.find(published=True)

    for worksheet in worksheets:
        new_worksheet = FakeWorksheetForMarks(
            worksheet.identifier, worksheet.name, worksheet.assessable,
            worksheet.published)
        if new_worksheet.assessable:
            # Calculate the user's score for this worksheet
            mand_done, mand_total, opt_done, opt_total = (
                ivle.worksheet.utils.calculate_score(store, user, worksheet))
            if opt_total > 0:
                optional_message = " (excluding optional exercises)"
            else:
                optional_message = ""
            if mand_done >= mand_total:
                new_worksheet.complete_class = "complete"
            elif mand_done > 0:
                new_worksheet.complete_class = "semicomplete"
            else:
                new_worksheet.complete_class = "incomplete"
            problems_done += mand_done
            problems_total += mand_total
            new_worksheet.mand_done = mand_done
            new_worksheet.total = mand_total
            new_worksheet.optional_message = optional_message
        new_worksheets.append(new_worksheet)

    return new_worksheets, problems_total, problems_done
