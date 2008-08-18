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

# Returns a JSON response string indicating the results.

import os
import time

import cjson

from common import (db, util)
import test
import conf

def handle(req):
    """Handler for Ajax backend TutorialService app."""
    # Set request attributes
    req.write_html_head_foot = False     # No HTML

    if req.path != "":
        req.throw_error(req.HTTP_BAD_REQUEST)
    fields = req.get_fieldstorage()
    act = fields.getfirst('action')
    exercise = fields.getfirst('exercise')
    if act is None or exercise is None:
        req.throw_error(req.HTTP_BAD_REQUEST)
    act = act.value
    exercise = exercise.value

    if act == 'save' or act == 'test':
        # Must be POST
        if req.method != 'POST':
            req.throw_error(req.HTTP_BAD_REQUEST)
        code = fields.getfirst('code')

        if code is None:
            req.throw_error(req.HTTP_BAD_REQUEST)
        code = code.value

        if act == 'save':
            handle_save(req, exercise, code, fields)
        else:   # act == "test"
            handle_test(req, exercise, code, fields)
    else:
        req.throw_error(req.HTTP_BAD_REQUEST)

def handle_save(req, exercise, code, fields):
    """Handles a save action. This saves the user's code without executing it.
    """
    # Need to open JUST so we know this is a real exercise.
    # (This avoids users submitting code for bogus exercises).
    exercisefile = util.open_exercise_file(exercise)
    if exercisefile is None:
        req.throw_error(req.HTTP_NOT_FOUND,
            "The exercise was not found.")
    exercisefile.close()

    req.write('{"result": "ok"}')

    conn = db.DB()

    try:
        conn.write_problem_save(
            login = req.user.login,
            exercisename = exercise,
            date = time.localtime(),
            text = code)
    finally:
        conn.close()

def handle_test(req, exercise, code, fields):
    """Handles a test action."""

    exercisefile = util.open_exercise_file(exercise)
    if exercisefile is None:
        req.throw_error(req.HTTP_NOT_FOUND,
            "The exercise was not found.")

    # Parse the file into a exercise object using the test suite
    exercise_obj = test.parse_exercise_file(exercisefile)
    exercisefile.close()
    # Run the test cases. Get the result back as a JSONable object.
    # Return it.
    test_results = exercise_obj.run_tests(code)

    conn = db.DB()
    try:
        conn.insert_problem_attempt(
            login = req.user.login,
            exercisename = exercise,
            date = time.localtime(),
            complete = test_results['passed'],
            attempt = code)

        # Query the DB to get an updated score on whether or not this problem
        # has EVER been completed (may be different from "passed", if it has
        # been completed before), and the total number of attempts.
        completed, attempts = conn.get_problem_status(req.user.login,
            exercise)
        test_results["completed"] = completed
        test_results["attempts"] = attempts

        req.write(cjson.encode(test_results))
    finally:
        conn.close()
