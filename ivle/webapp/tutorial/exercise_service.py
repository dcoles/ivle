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
from ivle.webapp.errors import NotFound, BadRequest
from ivle.webapp.tutorial.test.TestFramework import TestCreationError
from ivle.worksheet.utils import test_exercise_submission


class ExercisesRESTView(JSONRESTView):
    """Rest view for adding an exercise."""
    
    #Only lecturers, tutors and admins can add exercises
    def get_permissions(self, user):
        if user is not None:
            if user.admin:
                return set(['save'])
            elif 'lecturer' in set((e.role for e in user.active_enrolments)):
                return set(['save'])
            elif 'tutor' in set((e.role for e in user.active_enrolments)):
                return set(['save'])
            else:
                return set()
        else:
            return set()
    
    @named_operation('save')
    def add_exercise(self, req, identifier, name, description, partial, solution, include, num_rows):
    
        new_exercise = Exercise()
        new_exercise.id = unicode(identifier)
        new_exercise.name = unicode(name)
        new_exercise.description = unicode(description)
        new_exercise.partial = unicode(partial)
        new_exercise.solution = unicode(solution)
        new_exercise.include = unicode(include)
        new_exercise.num_rows = int(num_rows)
        
        req.store.add(new_exercise)
        
        return {'result': 'ok'}
        
        

class ExerciseRESTView(JSONRESTView):
    """View for updating Exercises"""
    
    @named_operation(u'edit')
    def edit_exercise(self, req, name, description, partial, 
                      solution, include, num_rows):
        
        self.context.name = unicode(name)
        self.context.description = unicode(description)
        self.context.partial = unicode(partial)
        self.context.solution = unicode(solution)
        self.context.include = unicode(include)
        self.context.num_rows = int(num_rows)
        return {'result': 'ok'}
    
    @named_operation(u'edit')
    def delete_exercise(self, req, id):
        
        self.context.delete()
        return {'result': 'ok'}

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
    def delete_suite(self, req, suiteid):
        
        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        if suite is None:
            raise NotFound()
        
        suite.delete()
        
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
        new_var.var_value = unicode(var_val)
        new_var.arg_no = int(argno) if len(argno) else None
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
            raise NotFound("Var not found.")
            
        var.var_type = unicode(var_type)
        var.var_name = unicode(var_name)
        var.var_value = unicode(var_val)
        var.arg_no = int(argno) if len(argno) else None
        
        return {'result': 'ok'}
    
    @named_operation(u'edit')
    def delete_var(self, req, suiteid, varid):
        var = req.store.find(TestSuiteVar,
            TestSuiteVar.varid == int(varid),
            TestSuiteVar.suiteid == int(suiteid)).one()
        if var is None:
            raise NotFound()
        
        var.delete()
        
        return {'result': 'ok'}
        
    @named_operation(u'edit')
    def add_testcase(self, req, suiteid, passmsg, failmsg):
        
        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        
        if suite is None:
            raise NotFound()
        
        new_case = TestCase()
        new_case.passmsg = unicode(passmsg)
        new_case.failmsg = unicode(failmsg)
        new_case.seq_no = suite.test_cases.count()
        suite.test_cases.add(new_case)
        
        req.store.add(new_case)
        
        return {'result': 'ok'}
    
    @named_operation(u'edit')
    def edit_testcase(self, req, suiteid, testid, passmsg, failmsg):
        
        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        if suite is None:
            raise NotFound()
        
        test_case = req.store.find(TestCase,
            TestCase.suiteid == suite.suiteid,
            TestCase.testid == int(testid)).one()
        if test_case is None:
            raise NotFound()
        
        test_case.passmsg = unicode(passmsg)
        test_case.failmsg = unicode(failmsg)
        
        return {'result': 'ok'}
    
    @named_operation(u'edit')
    def delete_testcase(self, req, suiteid, testid):
        
        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        if suite is None:
            raise NotFound()
        
        test_case = req.store.find(TestCase,
            TestCase.suiteid == suite.suiteid,
            TestCase.testid == int(testid)).one()
        if test_case is None:   
            raise NotFound()

        test_case.delete()

        return {'result': 'ok'}
    
    @named_operation(u'edit')
    def edit_testpart(self, req, suiteid, testid, partid, part_type, test_type, 
                      data):
    
        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        if suite is None:
            raise NotFound()
        
        test_case = req.store.find(TestCase,
            TestCase.suiteid == suite.suiteid,
            TestCase.testid == int(testid)).one()
        if test_case is None:
            raise NotFound()
        
        test_part = req.store.find(TestCasePart,
            TestCasePart.testid == test_case.testid,
            TestCasePart.partid == int(partid)).one()
        if test_part is None:
            raise NotFound('testcasepart')
        
        test_part.part_type = unicode(part_type)
        test_part.test_type = unicode(test_type)
        test_part.data = unicode(data)
        
        return {'result': 'ok'}
    
    @named_operation(u'edit')
    def add_testpart(self, req, suiteid, testid, part_type, test_type, 
                      data):
    
        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        if suite is None:
            raise NotFound()
        
        test_case = req.store.find(TestCase,
            TestCase.suiteid == suite.suiteid,
            TestCase.testid == int(testid)).one()
        if test_case is None:
            raise NotFound()
        
        test_part = TestCasePart()
        test_part.part_type = unicode(part_type)
        test_part.test_type = unicode(test_type)
        test_part.data = unicode(data)
        
        test_case.parts.add(test_part)
        
        return {'result': 'ok'}
    
    @named_operation(u'edit')
    def delete_testpart(self, req, suiteid, testid, partid):
        suite = req.store.find(TestSuite,
            TestSuite.suiteid == int(suiteid),
            TestSuite.exercise_id == self.context.id).one()
        if suite is None:
            raise NotFound()
        
        test_case = req.store.find(TestCase,
            TestCase.suiteid == suite.suiteid,
            TestCase.testid == int(testid)).one()
        if test_case is None:
            raise NotFound()
        
        test_part = req.store.find(TestCasePart,
            TestCasePart.testid == test_case.testid,
            TestCasePart.partid == int(partid)).one()
        if test_part is None:
            raise NotFound()
        
        test_part.delete()
        
        return {'result': 'ok'}

    @named_operation(u'edit')
    def test(self, req, code):
        try:
            return test_exercise_submission(
                req.config, req.user, self.context, code)
        except TestCreationError, e:
            return {'critical_error': {'name': 'TestCreationError', 'detail': e._reason}}
