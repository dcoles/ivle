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

import ivle.util
import ivle.console
import ivle.database
from ivle.database import Exercise, ExerciseAttempt, ExerciseSave, Worksheet, \
                          Offering, Subject, Semester, WorksheetExercise
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
        
        self.worksheet_exercise = req.store.find(WorksheetExercise,
            WorksheetExercise.exercise_id == exercise,
            WorksheetExercise.worksheet_id == Worksheet.id,
            Worksheet.offering_id == Offering.id,
            Offering.subject_id == Subject.id,
            Subject.code == subject,
            Offering.semester_id == Semester.id,
            Semester.year == year,
            Semester.semester == semester).one()
        
        self.context = self.user # XXX: Not quite right.

    @require_permission('edit')
    def GET(self, req):
        """Handles a GET Attempts action."""
        attempts = req.store.find(ExerciseAttempt, 
                ExerciseAttempt.ws_ex_id == self.worksheet_exercise.id,
                ExerciseAttempt.user_id == self.user.id)
        # attempts is a list of ExerciseAttempt objects. Convert to dictionaries
        time_fmt = lambda dt: datetime.datetime.strftime(dt, TIMESTAMP_FORMAT)
        attempts = [{'date': time_fmt(a.date), 'complete': a.complete}
                for a in attempts]

        return attempts


    @require_permission('edit')
    def PUT(self, req, data):
        """ Tests the given submission """
        exercise = req.store.find(Exercise, 
            Exercise.id == self.worksheet_exercise.exercise_id).one()
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
            worksheet_exercise = self.worksheet_exercise,
            date = datetime.datetime.now(),
            complete = test_results['passed'],
            text = unicode(data['code'])
        )

        req.store.add(attempt)

        # Query the DB to get an updated score on whether or not this problem
        # has EVER been completed (may be different from "passed", if it has
        # been completed before), and the total number of attempts.
        completed, attempts = ivle.worksheet.get_exercise_status(req.store,
            req.user, self.worksheet_exercise)
        test_results["completed"] = completed
        test_results["attempts"] = attempts

        return test_results


class AttemptRESTView(JSONRESTView):
    '''REST view of an exercise attempt.'''

    def __init__(self, req, subject, year, semester, worksheet, exercise, 
                 username, date):
        # TODO: Find exercise within worksheet.
        user = ivle.database.User.get_by_login(req.store, username)
        if user is None:
            raise NotFound()

        try:
            date = datetime.datetime.strptime(date, TIMESTAMP_FORMAT)
        except ValueError:
            raise NotFound()

        worksheet_exercise = req.store.find(WorksheetExercise,
            WorksheetExercise.exercise_id == exercise,
            WorksheetExercise.worksheet_id == Worksheet.id,
            Worksheet.identifier == worksheet,
            Worksheet.offering_id == Offering.id,
            Offering.subject_id == Subject.id,
            Subject.code == subject,
            Offering.semester_id == Semester.id,
            Semester.year == year,
            Semester.semester == semester).one()
            
        attempt = req.store.find(ExerciseAttempt,
            ExerciseAttempt.login_id == user.id,
            ExerciseAttempt.ws_ex_id == worksheet_exercise.id,
            ExerciseAttempt.date == date
        )

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
        # XXX: Does any user have the ability to save as themselves?
        # XXX: Does a user EVER have permission to save as another user?
        if user is not None:
            return set(['save'])
        else:
            return set()

    @named_operation('save')
    def save(self, req, text):
        # Find the appropriate WorksheetExercise to save to. If its not found,
        # the user is submitting against a non-existant worksheet/exercise
        worksheet_exercise = req.store.find(WorksheetExercise,
            WorksheetExercise.exericise_id == self.exercise,
            WorksheetExercise.worksheet_id == Worksheet.id,
            Worksheet.offering_id == Offering.id,
            Offering.subject_id == Subject.id,
            Subject.code == self.subject,
            Offering.semester_id == Semester.id,
            Semester.year == self.year,
            Semester.semester == self.semester).one()
        
        if worksheet_exercise is None:
            raise NotFound()

        new_save = ExerciseSave()
        new_save.worksheet_exercise = worksheet_exercise
        new_save.user = req.user
        new_save.text = unicode(text)
        new_save.date = datetime.datetime.now()
        req.store.add(new_save)
        return {"result": "ok"}


class WorksheetRESTView(JSONRESTView):
    """View used to update a worksheet."""

    def generate_exerciselist(self, req, worksheet):
        """Runs through the worksheetstream, generating the appropriate
        WorksheetExercises, and de-activating the old ones."""
        exercises = []
        # Turns the worksheet into an xml stream, and then finds all the 
        # exercise nodes in the stream.
        worksheet = genshi.XML(worksheet)
        for kind, data, pos in worksheet:
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
        db_worksheet_exercises = req.store.find(WorksheetExercise,
            WorksheetExercise.worksheet_id == self.context.id)
        for worksheet_exercise in db_worksheet_exercises:
            worksheet_exercise.active = False
        
        for exerciseid, optional in exercises:
            worksheet_exercise = req.store.find(WorksheetExercise,
                WorksheetExercise.worksheet_id == self.context.id,
                Exercise.id == WorksheetExercise.exercise_id,
                Exercise.id == exerciseid).one()
            if worksheet_exercise is None:
                exercise = req.store.find(Exercise,
                    Exercise.id == exerciseid
                ).one()
                if exercise is None:
                    raise NotFound()
                worksheet_exercise = WorksheetExercise()
                worksheet_exercise.worksheet_id = self.context.id
                worksheet_exercise.exercise_id = exercise.id
                req.store.add(worksheet_exercise)
            worksheet_exercise.active = True
            worksheet_exercise.seq_no = ex_num
            worksheet_exercise.optional = optional

    def get_permissions(self, user):
        # XXX: Do it properly.
        # XXX: Lecturers should be allowed to add worksheets Only to subjects
        #      under their control
        if user is not None:
            if user.rolenm == 'admin':
                return set(['save'])
            else:
                return set()
        else:
            return set()    

    def __init__(self, req, **kwargs):
    
        self.worksheet = kwargs['worksheet']
        self.subject = kwargs['subject']
        self.year = kwargs['year']
        self.semester = kwargs['semester']
    
        self.context = req.store.find(Worksheet,
            Worksheet.identifier == self.worksheet,
            Worksheet.offering_id == Offering.id,
            Offering.subject_id == Subject.id,
            Subject.code == self.subject,
            Offering.semester_id == Semester.id,
            Semester.year == self.year,
            Semester.semester == self.semester).one()
        
        if self.context is None:
            raise NotFound()
    
    @named_operation('save')
    def save(self, req, name, assessable, data):
        """Takes worksheet data and saves it."""
        self.generate_exerciselist(req, data)
        
        self.context.name = unicode(name)
        self.context.data = unicode(data)
        self.context.assessable = self.convert_bool(assessable)
        
        return {"result": "ok"}
