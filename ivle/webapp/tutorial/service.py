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

import datetime

import genshi
from storm.locals import Store

import ivle.database
from ivle.database import Exercise, ExerciseAttempt, ExerciseSave, Worksheet, \
                          Offering, Subject, Semester, User, WorksheetExercise
import ivle.worksheet.utils
from ivle.webapp.base.rest import (JSONRESTView, write_operation,
                                   require_permission)
from ivle.webapp.errors import NotFound


TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


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
        # Trim off any trailing whitespace (can cause syntax errors in python)
        # While technically this is a user error, it causes a lot of confusion 
        # for student since it's "invisible".
        code = data['code'].rstrip()

        test_results = ivle.worksheet.utils.test_exercise_submission(
            req.config, req.user, self.context.worksheet_exercise.exercise,
            code)

        attempt = ivle.database.ExerciseAttempt(user=req.user,
            worksheet_exercise = self.context.worksheet_exercise,
            date = datetime.datetime.now(),
            complete = test_results['passed'],
            text = unicode(code)
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

    @write_operation('view')
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


class WorksheetsRESTView(JSONRESTView):
    """View used to update and create Worksheets."""

    @write_operation('edit_worksheets')
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

    @write_operation('edit_worksheets')
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
