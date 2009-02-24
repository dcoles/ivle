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

# Author: Nick Chadwick


import ivle.database
from ivle.database import Exercise, TestSuite, TestCase, \
                          TestSuiteVar, TestCasePart
from ivle.webapp.base.rest import (JSONRESTView, named_operation,
                                   require_permission)
from ivle.webapp.errors import NotFound


class ExercisesRESTView(JSONRESTView):
    """Rest view for adding an exercise."""
    
    #Only lecturers and admins can add exercises
    def get_permissions(self, user):
        if user is not None:
            if user.rolenm in ('admin', 'lecturer'):
                return set(['save'])
            else:
                return set()
        else:
            return set()
    
    @named_operation('save')
    def add_exercise(self, req, identifier, name, description, partial, solution, include, num_rows):
    
        new_exercise = Exercise()
        new_exercise.id = unicode(identifier)
        new_exercise.description = description
        new_exercise.partial = partial
        new_exercise.solution = solution
        new_exercise.include = include
        new_exercise.num_rows = num_rows
        
        req.store.add(new_exercise)
        
        return {'result': 'ok'}
        
        

class ExerciseRESTView(JSONRESTView):
    """View for updating Exercises"""
    
    def get_permissions(self, user):
        if user is not None:
            if user.rolenm in ('admin', 'lecturer'):
                return set(['edit'])
            else:
                return set()
        else:
            return set()
    
    def __init__(self, req, exercise):
        
        self.context = req.store.find(Exercise,
            Exercise.id == exercise).one()
        
        if self.context is None:
            raise NotFound()

    @named_operation('edit')
    def update_exercise(self, req, name, description, partial, 
                      solution, include, num_rows):
        
        self.context.name = unicode(name)
        self.context.description = unicode(description)
        self.context.partial = unicode(partial)
        self.context.solution = unicode(solution)
        self.context.include = unicode(include)
        self.context.num_rows = int(num_rows)
        
        return {'result': 'ok'}
        
    @named_operation('edit')
    def add_suite(self, req, description, seq_no, function, stdin):
        
        new_suite = TestSuite()
        new_suite.description = description
        new_suite.seq_no = seq_no
        new_suite.function = function
        new_suite.stdin = stdin
        new_suite.exercise = self.context
        
        req.store.add(new_suite)
        
        return {'result': 'ok'}
        

class TestSuiteRESTView():
    """View for updating Test Suites, adding variable and adding test parts."""
    
    def get_permissions(self, user):
        if user is not None:
            if user.rolenm in ('admin', 'lecturer'):
                return set(['edit'])
            else:
                return set()
        else:
            return set()

    @named_operation('edit')
    def edit_testsuite(self, req, suiteid):
        
        test_suite = req.store.find(TestSuite, 
            TestSuite.suite.id == suiteid).one()
        
        if test_suite is not None:
            raise NotFound()
        
        return {'result': 'NOT IMPLEMENTED'}
