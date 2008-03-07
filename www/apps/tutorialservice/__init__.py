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

# "exercise" - The path to a exercise file (including the .xml extension),
#    relative to the subjects base directory.
# "code" - Full text of the student's code being submitted.
# "action". May be "test". (More to come).

# Returns a JSON response string indicating the results.

import os
import time

import cjson

from common import db
import test
import conf

def handle(req):
    """Handler for Ajax backend TutorialService app."""
    # Set request attributes
    req.write_html_head_foot = False     # No HTML

    if req.path != "":
        req.throw_error(req.HTTP_BAD_REQUEST)
    # Get all the arguments, if POST.
    # Ignore arguments if not POST, since we aren't allowed to cause
    # side-effects on the server.
    fields = req.get_fieldstorage()
    act = fields.getfirst('action')
    exercise = fields.getfirst('exercise')
    code = fields.getfirst('code')

    if exercise == None or code == None or act == None:
        req.throw_error(req.HTTP_BAD_REQUEST)
    act = act.value
    exercise = exercise.value
    code = code.value

    if act == "test":
        handle_test(req, exercise, code, fields)
    elif act == "run":
        handle_run(req, exercise, code, fields)
    else:
        req.throw_error(req.HTTP_BAD_REQUEST)

def handle_test(req, exercise, code, fields):
    """Handles a test action."""

    # First normalise the path
    exercise = os.path.normpath(exercise)
    # Now if it begins with ".." or separator, then it's illegal
    if exercise.startswith("..") or exercise.startswith(os.sep):
        exercisefile = None
    else:
        exercisefile = os.path.join(conf.exercises_base, exercise)

    try:
        exercisefile = open(exercisefile)
    except (TypeError, IOError):    # TypeError if exercisefile == None
        req.throw_error(req.HTTP_NOT_FOUND)

    # Parse the file into a exercise object using the test suite
    exercise_obj = test.parse_exercise_file(exercisefile)
    exercisefile.close()
    # Run the test cases. Get the result back as a JSONable object.
    # Return it.
    test_results = exercise_obj.run_tests(code)
    req.write(cjson.encode(test_results))

    conn = db.DB()

    try:
        x = conn.get_single({'identifier':exercise},
                            'problem', ['problemid'], ['identifier'])
        problemid = x['problemid']
    except Exception, e:
        # if we failed to get a problemid, it was probably because
        # the exercise wasn't in the db. So lets insert it!
        #
        # The insert can fail if someone else simultaneously does
        # the insert, so if the insert fails, we ignore the problem. 
        try:
            conn.insert({'identifier': exercise}, 'problem',
                    set(['identifier']))
        except Exception, e:
            pass

        # Assuming the insert succeeded, we should be able to get the
        # problemid now.
        x = conn.get_single({'identifier':exercise},
                            'problem', ['problemid'], ['identifier'])
        problemid = x['problemid']

    x = conn.get_single({'login':req.user.login},
                        'login', ['loginid'], ['login'])
    loginid = x['loginid']

    rec = {}
    rec['problemid'] = problemid
    rec['loginid'] = loginid
    rec['date'] = time.localtime()
    rec['complete'] = test_results['passed']
    rec['attempt'] = code

    print >> open("/tmp/attempts.txt", "a"), repr(rec)

    conn.insert(rec, 'problem_attempt',
                set(['problemid','loginid','date','complete','attempt']))

def handle_run(req, exercise, code, fields):
    """Handles a run action."""
    # Extremely makeshift.
    # For now, just echo the code back
    output = code
    out_json = {"stdout": output}
    req.write(cjson.encode(out_json))
