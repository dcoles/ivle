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

# Author: Matt Giuca, Nick Chadwick

'''AJAX backend for the tutorial application.'''

import os
import datetime

import genshi
from storm.locals import Store

import ivle.console
import ivle.database
from ivle.database import Exercise, ExerciseAttempt, ExerciseSave, Worksheet, \
                          Offering, Subject, Semester, User, WorksheetExercise
import ivle.worksheet.utils
import ivle.webapp.tutorial.test
from ivle.webapp.base.rest import (JSONRESTView, named_operation,
                                   require_permission)
from ivle.webapp.errors import NotFound

# If True, getattempts or getattempt will allow browsing of inactive/disabled
# attempts. If False, will not allow this.
HISTORY_ALLOW_INACTIVE = False

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


class ExerciseAttempts(object):
    """The set of exercise attempts for a user and exercise.

    A combination of a User and WorksheetExercise, this provides access to
    the User's ExerciseAttempts.
    """

    def __init__(self, worksheet_exercise, user):
        self.worksheet_exercise = worksheet_exercise
        self.user = user

    def get_permissions(self, user):
        return self.user.get_permissions(user)


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


def worksheet_exercise_to_user_attempts(worksheet_exercise, login):
    user = User.get_by_login(Store.of(worksheet_exercise), login)
    if user is None:
        return None
    return ExerciseAttempts(worksheet_exercise, user)


def worksheet_to_worksheet_exercise(worksheet, exercise_name):
    return Store.of(worksheet).find(
        WorksheetExercise,
        WorksheetExercise.exercise_id == exercise_name,
        WorksheetExercise.worksheet == worksheet
        ).one()


class AttemptsRESTView(JSONRESTView):
    '''REST view of a user's attempts at an exercise.'''

    @require_permission('edit')
    def GET(self, req):
        """Handles a GET Attempts action."""
        attempts = req.store.find(ExerciseAttempt, 
                ExerciseAttempt.ws_ex_id == self.context.worksheet_exercise.id,
                ExerciseAttempt.user_id == self.context.user.id)
        # attempts is a list of ExerciseAttempt objects. Convert to dictionaries
        time_fmt = lambda dt: datetime.datetime.strftime(dt, TIMESTAMP_FORMAT)
        attempts = [{'date': time_fmt(a.date), 'complete': a.complete}
                for a in attempts]

        return attempts


    @require_permission('edit')
    def PUT(self, req, data):
        """ Tests the given submission """
        # Start a console to run the tests on
        jail_path = os.path.join(req.config['paths']['jails']['mounts'],
                                 req.user.login)
        working_dir = os.path.join("/home", req.user.login)
        cons = ivle.console.Console(req.config, req.user.unixid, jail_path,
                                    working_dir)

        # Parse the file into a exercise object using the test suite
        exercise_obj = ivle.webapp.tutorial.test.parse_exercise_file(
                            self.context.worksheet_exercise.exercise, cons)

        # Run the test cases. Get the result back as a JSONable object.
        # Return it.
        test_results = exercise_obj.run_tests(data['code'])

        # Close the console
        cons.close()

        attempt = ivle.database.ExerciseAttempt(user=req.user,
            worksheet_exercise = self.context.worksheet_exercise,
            date = datetime.datetime.now(),
            complete = test_results['passed'],
            text = unicode(data['code'])
        )

        req.store.add(attempt)

        # Query the DB to get an updated score on whether or not this problem
        # has EVER been completed (may be different from "passed", if it has
        # been completed before), and the total number of attempts.
        completed, attempts = ivle.worksheet.utils.get_exercise_status(
                req.store, req.user, self.context.worksheet_exercise)
        test_results["completed"] = completed
        test_results["attempts"] = attempts

        return test_results


class AttemptRESTView(JSONRESTView):
    '''REST view of an exercise attempt.'''

    @require_permission('view')
    def GET(self, req):
        return {'code': self.context.text}


class WorksheetExerciseRESTView(JSONRESTView):
    '''REST view of a worksheet exercise.'''

    @named_operation('view')
    def save(self, req, text):
        # Find the appropriate WorksheetExercise to save to. If its not found,
        # the user is submitting against a non-existant worksheet/exercise

        old_save = req.store.find(ExerciseSave,
            ExerciseSave.ws_ex_id == self.context.id,
            ExerciseSave.user == req.user).one()
        
        #Overwrite the old, or create a new if there isn't one
        if old_save is None:
            new_save = ExerciseSave()
            req.store.add(new_save)
        else:
            new_save = old_save
        
        new_save.worksheet_exercise = self.context
        new_save.user = req.user
        new_save.text = unicode(text)
        new_save.date = datetime.datetime.now()

        return {"result": "ok"}


# Note that this is the view of an existing worksheet. Creation is handled
# by OfferingRESTView (as offerings have worksheets)
class WorksheetRESTView(JSONRESTView):
    """View used to update a worksheet."""

    @named_operation('edit')
    def save(self, req, name, assessable, data, format):
        """Takes worksheet data and saves it."""
        self.context.name = unicode(name)
        self.context.assessable = self.convert_bool(assessable)
        self.context.data = unicode(data)
        self.context.format = unicode(format)
        ivle.worksheet.utils.update_exerciselist(self.context)
        
        return {"result": "ok"}

class WorksheetsRESTView(JSONRESTView):
    """View used to update and create Worksheets."""

    @named_operation('edit')
    def add_worksheet(self, req, identifier, name, assessable, data, format):
        """Takes worksheet data and adds it."""
        
        new_worksheet = Worksheet()
        new_worksheet.seq_no = self.context.worksheets.count()
        # Setting new_worksheet.offering implicitly adds new_worksheet,
        # hence worksheets.count MUST be called above it
        new_worksheet.offering = self.context
        new_worksheet.identifier = unicode(identifier)
        new_worksheet.name = unicode(name)
        new_worksheet.assessable = self.convert_bool(assessable)
        new_worksheet.data = unicode(data)
        new_worksheet.format = unicode(format)
        
        # This call is added for clarity, as the worksheet is implicitly added.        
        req.store.add(new_worksheet)

        ivle.worksheet.utils.update_exerciselist(new_worksheet)

        return {"result": "ok"}

    @named_operation('edit')
    def move_up(self, req, worksheetid):
        """Takes a list of worksheet-seq_no pairs and updates their 
        corresponding Worksheet objects to match."""
        
        worksheet_below = req.store.find(Worksheet,
            Worksheet.offering_id == self.context.id,
            Worksheet.identifier == unicode(worksheetid)).one()
        if worksheet_below is None:
            raise NotFound('worksheet_below')
        worksheet_above = req.store.find(Worksheet,
            Worksheet.offering_id == self.context.id,
            Worksheet.seq_no == (worksheet_below.seq_no - 1)).one()
        if worksheet_above is None:
            raise NotFound('worksheet_above')

        worksheet_below.seq_no = worksheet_below.seq_no - 1
        worksheet_above.seq_no = worksheet_above.seq_no + 1
        
        return {'result': 'ok'}

    @named_operation('edit')
    def move_down(self, req, worksheetid):
        """Takes a list of worksheet-seq_no pairs and updates their 
        corresponding Worksheet objects to match."""
        
        worksheet_above = req.store.find(Worksheet,
            Worksheet.offering_id == self.context.id,
            Worksheet.identifier == unicode(worksheetid)).one()
        if worksheet_above is None:
            raise NotFound('worksheet_below')
        worksheet_below = req.store.find(Worksheet,
            Worksheet.offering_id == self.context.id,
            Worksheet.seq_no == (worksheet_above.seq_no + 1)).one()
        if worksheet_below is None:
            raise NotFound('worksheet_above')

        worksheet_below.seq_no = worksheet_below.seq_no - 1
        worksheet_above.seq_no = worksheet_above.seq_no + 1
        
        return {'result': 'ok'}
