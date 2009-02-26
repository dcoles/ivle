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
            if user.admin:
                return set(['save'])
            elif user in set((e.role for e in req.user.active_enrolments)):
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
            if user.admin:
                return set([u'edit'])
            elif user in set((e.role for e in req.user.active_enrolments)):
                return set([u'edit'])
            else:
                return set()
        else:
            return set()
    
    def __init__(self, req, exercise):
        
        self.context = req.store.find(Exercise,
            Exercise.id == exercise).one()
        
        if self.context is None:
            raise NotFound()

    @named_operation(u'edit')
    def edit_exercise(self, req, name, description, partial, 
                      solution, include, num_rows):
        
        self.context.name = unicode(name)
        self.context.description = unicode(description)
        self.context.partial = unicode(partial)
        self.context.solution = unicode(solution)
        self.context.include = unicode(include)
        self.context.num_rows = int(num_rows)
        return {'result': 'moo'}
        
    @named_operation(u'edit')
    def add_suite(self, req, description, function, stdin):
        
        new_suite = TestSuite()
        new_suite.description = unicode(description)
        new_suite.seq_no = self.context.test_suites.count()
        new_suite.function = unicode(function)
        new_suite.stdin = unicode(stdin)
        new_suite.exercise = self.context
        
        req.store.add(new_suite)
        
        return {'result': 'ok'}
        
    @named_operation(u'edit')
    def edit_suite(self, req, suiteid, description, function, stdin):
        
        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        
        if suite is None:
            raise NotFound()
        
        suite.description = unicode(description)
        suite.function = unicode(function)
        suite.stdin = unicode(stdin)
        
        return {'result': 'ok'}
      
    @named_operation(u'edit')
    def add_var(self, req, suiteid, var_type, var_name, var_val, argno):

        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        
        if suite is None:
            raise NotFound()
        
        new_var = TestSuiteVar()
        new_var.var_type = unicode(var_type)
        new_var.var_name = unicode(var_name)
        new_var.var_val = unicode(var_val)
        new_var.argno = argno
        new_var.suite = suite
        
        req.store.add(new_var)
        
        return {'result': 'ok'}

    @named_operation(u'edit')
    def edit_var(self, req, suiteid, varid, var_type, var_name, var_val, argno):
        var = req.store.find(TestSuiteVar,
            TestSuiteVar.varid == int(varid),
            TestSuiteVar.suiteid == int(suiteid)
        ).one()
        
        if var is None:
            raise NotFound()
            
        var.var_type = unicode(var_type)
        var.var_name = unicode(var_name)
        var.var_val = unicode(var_val)
        var.argno = int(argno)
        
        return {'result': 'ok'}
    
    @named_operation(u'edit')
    def add_testcase(self, req, suiteid, passmsg, failmsg, default):
        
        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        
        if suite is None:
            raise NotFound()
        
        new_case = TestCase()
        new_case.passmsg = unicode(passmsg)
        new_case.failmsg = unicode(failmsg)
        new_case.default = unicode(default)
        new_case.seq_no = suite.test_cases.count()
        suite.test_cases.add(new_case)
        
        req.store.add(new_case)
        
        return {'result': 'ok'}
