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

import ivle.util
import ivle.console
import ivle.database
from ivle.database import Exercise, ExerciseAttempt, ExerciseSave
import ivle.worksheet
import ivle.conf
import ivle.webapp.tutorial.test

from ivle.webapp.base.rest import (JSONRESTView, named_operation,
                                   require_permission)
from ivle.webapp.errors import NotFound

# If True, getattempts or getattempt will allow browsing of inactive/disabled
# attempts. If False, will not allow this.
HISTORY_ALLOW_INACTIVE = False

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


class AttemptsRESTView(JSONRESTView):
    '''REST view of a user's attempts at an exercise.'''
    def __init__(self, req, subject, year, semester, worksheet, 
                                                exercise, username):
        self.user = ivle.database.User.get_by_login(req.store, username)
        if self.user is None:
            raise NotFound()
        self.exercise = exercise
        
        self.context = self.user # XXX: Not quite right.

    @require_permission('edit')
    def GET(self, req):
        """Handles a GET Attempts action."""
        exercise = req.store.find(Exercise, Exercise.id == self.exercise).one()

        attempts = req.store.find(ExerciseAttempt, 
                ExerciseAttempt.exercise_id == exercise.id,
                ExerciseAttempt.user_id == self.user.id)
        # attempts is a list of ExerciseAttempt objects. Convert to dictionaries
        time_fmt = lambda dt: datetime.datetime.strftime(dt, TIMESTAMP_FORMAT)
        attempts = [{'date': time_fmt(a.date), 'complete': a.complete}
                for a in attempts]

        return attempts


    @require_permission('edit')
    def PUT(self, req, data):
        """ Tests the given submission """
        exercise = req.store.find(Exercise, Exercise.id == self.exercise).one()
        if exercise is None:
            raise NotFound()

        # Start a console to run the tests on
        jail_path = os.path.join(ivle.conf.jail_base, req.user.login)
        working_dir = os.path.join("/home", req.user.login)
        cons = ivle.console.Console(req.user.unixid, jail_path, working_dir)

        # Parse the file into a exercise object using the test suite
        exercise_obj = ivle.webapp.tutorial.test.parse_exercise_file(
                                                            exercise, cons)

        # Run the test cases. Get the result back as a JSONable object.
        # Return it.
        test_results = exercise_obj.run_tests(data['code'])

        # Close the console
        cons.close()

        attempt = ivle.database.ExerciseAttempt(user=req.user,
                                                exercise=exercise,
                                                date=datetime.datetime.now(),
                                                complete=test_results['passed'],
                                                # XXX
                                                text=unicode(data['code']))

        req.store.add(attempt)

        # Query the DB to get an updated score on whether or not this problem
        # has EVER been completed (may be different from "passed", if it has
        # been completed before), and the total number of attempts.
        completed, attempts = ivle.worksheet.get_exercise_status(req.store,
            req.user, exercise)
        test_results["completed"] = completed
        test_results["attempts"] = attempts

        return test_results


class AttemptRESTView(JSONRESTView):
    '''REST view of an exercise attempt.'''

    def __init__(self, req, subject, worksheet, exercise, username, date):
        # TODO: Find exercise within worksheet.
        user = ivle.database.User.get_by_login(req.store, username)
        if user is None:
            raise NotFound()

        try:
            date = datetime.datetime.strptime(date, TIMESTAMP_FORMAT)
        except ValueError:
            raise NotFound()

        exercise = ivle.database.Exercise.get_by_name(req.store, exercise)
        attempt = ivle.worksheet.get_exercise_attempt(req.store, user,
            exercise, as_of=date, allow_inactive=HISTORY_ALLOW_INACTIVE)

        if attempt is None:
            raise NotFound()

        self.context = attempt

    @require_permission('view')
    def GET(self, req):
        return {'code': self.context.text}


class ExerciseRESTView(JSONRESTView):
    '''REST view of an exercise.'''

    def get_permissions(self, user):
        # XXX: Do it properly.
        if user is not None:
            return set(['save'])
        else:
            return set()

    @named_operation('save')
    def save(self, req, text):
        # Need to open JUST so we know this is a real exercise.
        # (This avoids users submitting code for bogus exercises).
        exercise = req.store.find(Exercise,
            Exercise.id == self.exercise).one()
        ivle.worksheet.save_exercise(req.store, req.user, exercise,
                                     unicode(text), datetime.datetime.now())
        return {"result": "ok"}
