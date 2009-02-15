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

# Module: parse_exercise
# Author: Dilshan Angampitiya
#         Steven Bird (revisions)
# Date:   24/1/2008

"""
This file provides the function parse_exercise_file which takes an xml
specification of an exercise file and returns a test suite object for
that exercise. It throws a ParseException if there was a problem
parsing the file.
"""

from xml.dom.minidom import *
from TestFramework import *

DEFAULT_TEST_TYPE = 'norm'
DEFAULT_CASE_TYPE = 'match'

class ParseException(Exception):
    " Error when parsing the xml exercise file "
    def __init___(self, reason):
        self._reason = reason

    def __str__(self):
        return self._reason

def getTextData(element):
    """ Get the text and cdata inside an element
    Leading and trailing whitespace are stripped
    """
    data = ''
    for child in element.childNodes:
        if child.nodeType == child.CDATA_SECTION_NODE:
            data += child.data
        if child.nodeType == child.TEXT_NODE:
            data += child.data

    return data.strip()

def getCasePartData(partNode):
    """ Create an TestCasePart instance from test part xml data
    """
    
    func_pass = partNode.getAttribute('pass')
    func_fail = partNode.getAttribute('fail')
    default = partNode.getAttribute('default')
    if default == '': default = DEFAULT_CASE_TYPE
    
    part = TestCasePart(func_pass, func_fail, default)

    for child in partNode.childNodes:
        if child.nodeType != child.ELEMENT_NODE:
            continue

        if child.tagName == 'stdout':
            test_type = child.getAttribute('type')
            if test_type == '': test_type = DEFAULT_TEST_TYPE
            part.add_stdout_test(getTextData(child), test_type)
        elif child.tagName == 'stderr':
            test_type = child.getAttribute('type')
            if test_type == '': test_type = DEFAULT_TEST_TYPE
            part.add_stderr_test(getTextData(child), test_type)
        elif child.tagName == 'result':
            test_type = child.getAttribute('type')
            if test_type == '': test_type = DEFAULT_TEST_TYPE
            part.add_result_test(getTextData(child), test_type)
        elif child.tagName == 'exception':
            test_type = child.getAttribute('type')
            if test_type == '': test_type = DEFAULT_TEST_TYPE
            part.add_exception_test(getTextData(child), test_type)
        elif child.tagName == 'file':
            test_type = child.getAttribute('type')
            if test_type == '': test_type = DEFAULT_TEST_TYPE
            filename = child.getAttribute('name')
            if filename == '':
                raise ParseException("File without name in case %s" %case_name)
            part.add_file_test(filename, getTextData(child), test_type)
        elif child.tagName == 'code':
            test_type = child.getAttribute('type')
            if test_type == '': test_type = DEFAULT_TEST_TYPE
            part.add_code_test(getTextData(child), test_type)

    return part

def getCaseData(caseNode, console):
    """ Create a TestCase instance from test case xml data
    """
    
    case_name = caseNode.getAttribute('name')
    function = caseNode.getAttribute('function')
    if function == '': function = None
    case = TestCase(console, case_name, function)
    
    for child in caseNode.childNodes:
        if child.nodeType != child.ELEMENT_NODE:
            continue

        if child.tagName == 'stdin':
            # standard input
            case.set_stdin(getTextData(child))
        elif child.tagName == 'file':
            # file
            filename = child.getAttribute('name')
            if filename == '':
                raise ParseException("File without name in case %s" %case_name)
            case.add_file(filename, getTextData(child))
        elif child.tagName == 'var':
            # global variable
            var_name = child.getAttribute('name')
            var_val = child.getAttribute('value')
            if not var_name or not var_val:
                raise ParseException("Incomplete variable in case %s" %case_name)
            case.add_variable(var_name, var_val)
        elif child.tagName == 'arg':
            # function argument
            arg_val = child.getAttribute('value')
            arg_name = child.getAttribute('name')
            if arg_name == '': arg_name = None
            
            if not arg_val:
                raise ParseException("Incomplete argument in case %s" %case_name)
            case.add_arg(arg_val, arg_name)
        elif child.tagName == 'exception':
            exception_name = child.getAttribute('name')
            if not exception_name:
                raise ParseException("Incomplete exception in case %s" %case_name)
            case.add_exception(exception_name)
        elif child.tagName == 'function':
            # specify a test case part
            case.add_part(getCasePartData(child))

    return case
                
def parse_exercise_file(fileobj, console, exercise_num=1):
    """ Parse an xml exercise file and return a testsuite for that exercise """
    dom = parse(fileobj)

    # get exercise
    count = 0
    exercise = None
    for child in dom.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.tagName == 'exercise':
            count += 1
            if count == exercise_num:
                exercise = child
                break

    if exercise == None:
        raise ParseException("Not enough exercises")

    # get name
    exercise_name = exercise.getAttribute('name')
    if not exercise_name:
        raise ParseException('Exercise name not supplied')

    exercise_suite = TestSuite(exercise_name, console)

    # get solution and include info
    for child in exercise.childNodes:
        if child.nodeType != child.ELEMENT_NODE:
            continue
        if child.tagName == 'solution':
            exercise_suite.add_solution(getTextData(child))
        elif child.tagName == 'include':
            exercise_suite.add_include_code(getTextData(child))
        elif child.tagName == 'case':
            exercise_suite.add_case(getCaseData(child, console))

    return exercise_suite

