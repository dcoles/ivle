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

# Module: TutorialService
# Author: Matt Giuca
# Date:   25/1/2008

# Provides the AJAX backend for the tutorial application.
# This allows several actions to be performed on the code the student has
# typed into one of the exercise boxes.

# Calling syntax
# Path must be empty.
# The arguments determine what is to be done on this file.

# "action". One of the tutorialservice actions.
# "exercise" - The path to a exercise file (including the .xml extension),
#              relative to the subjects base directory.
# action "save" or "test" (POST only):
#   "code" - Full text of the student's code being submitted.
# action "getattempts": No arguments. Returns a list of
#   {'date': 'formatted_date', 'complete': bool} dicts.
# action "getattempt":
#   "date" - Formatted date. Gets most recent attempt before (and including)
#   that date.
#   Returns JSON string containing code, or null.

# Returns a JSON response string indicating the results.

import os
import time
import datetime

import cjson

from ivle import util
from ivle import console
import ivle.database
import ivle.worksheet
import ivle.conf
import ivle.webapp.tutorial.test # XXX: Really .test, not real test.

from ivle.webapp.base.rest import JSONRESTView
import ivle.database
from ivle.webapp.base.rest import named_operation

# If True, getattempts or getattempt will allow browsing of inactive/disabled
# attempts. If False, will not allow this.
HISTORY_ALLOW_INACTIVE = False

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


class AttemptsRESTView(JSONRESTView):
    '''
    Class to return a list of attempts for a given exercise, or add an Attempt
    '''
    def GET(self, req):
        """Handles a GET Attempts action."""
        exercise = ivle.database.Exercise.get_by_name(req.store, 
                                                        self.exercise)
        user = ivle.database.User.get_by_login(req.store, self.username)

        attempts = ivle.worksheet.get_exercise_attempts(req.store, user,
                            exercise, allow_inactive=HISTORY_ALLOW_INACTIVE)
        # attempts is a list of ExerciseAttempt objects. Convert to dictionaries
        time_fmt = lambda dt: datetime.datetime.strftime(dt, TIMESTAMP_FORMAT)
        attempts = [{'date': time_fmt(a.date), 'complete': a.complete}
                for a in attempts]
                
        return attempts
        
    def PUT(self, req, data):
        ''' Tests the given submission '''
        exercisefile = util.open_exercise_file(self.exercise)
        if exercisefile is None:
            req.throw_error(req.HTTP_NOT_FOUND,
                "The exercise was not found.")

        # Start a console to run the tests on
        jail_path = os.path.join(ivle.conf.jail_base, req.user.login)
        working_dir = os.path.join("/home", req.user.login)
        cons = console.Console(req.user.unixid, jail_path, working_dir)

        # Parse the file into a exercise object using the test suite
        exercise_obj = ivle.webapp.tutorial.test.parse_exercise_file(
                                                            exercisefile, cons)
        exercisefile.close()

        # Run the test cases. Get the result back as a JSONable object.
        # Return it.
        test_results = exercise_obj.run_tests(data['code'])

        # Close the console
        cons.close()

        # Get the Exercise from the database
        exercise = ivle.database.Exercise.get_by_name(req.store, self.exercise)

        attempt = ivle.database.ExerciseAttempt(user=req.user,
                                                exercise=exercise,
                                                date=datetime.datetime.now(),
                                                complete=test_results['passed'],
                                                # XXX
                                                text=unicode(data['code']))

        req.store.add(attempt)
        req.store.commit()
        # Query the DB to get an updated score on whether or not this problem
        # has EVER been completed (may be different from "passed", if it has
        # been completed before), and the total number of attempts.
        completed, attempts = ivle.worksheet.get_exercise_status(req.store,
            req.user, exercise)
        test_results["completed"] = completed
        test_results["attempts"] = attempts

        return test_results
        

class AttemptRESTView(JSONRESTView):
    '''
    View used to extract the data of a specified attempt
    '''
    
    def GET(self, req):
        # Get an actual date object, rather than a string
        date = datetime.datetime.strptime(self.date, TIMESTAMP_FORMAT)
        
        exercise = ivle.database.Exercise.get_by_name(req.store, self.exercise)
        attempt = ivle.worksheet.get_exercise_attempt(req.store, req.user,
            exercise, as_of=date, allow_inactive=HISTORY_ALLOW_INACTIVE)
        if attempt is not None:
            attempt = attempt.text
        # attempt may be None; will write "null"
        return {'code': attempt}
        
class ExerciseRESTView(JSONRESTView):
    '''
    Handles a save action. This saves the user's code without executing it.
    '''
    @named_operation
    def save(self, req, text):
        # Need to open JUST so we know this is a real exercise.
        # (This avoids users submitting code for bogus exercises).
        exercisefile = util.open_exercise_file(self.exercise)
        if exercisefile is None:
            req.throw_error(req.HTTP_NOT_FOUND,
                "The exercise was not found.")
        exercisefile.close()

        exercise = ivle.database.Exercise.get_by_name(req.store, self.exercise)
        ivle.worksheet.save_exercise(req.store, req.user, exercise,
                                     unicode(text), datetime.datetime.now())
        req.store.commit()
        return {"result": "ok"}
