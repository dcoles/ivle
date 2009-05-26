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

# Module: TestFramework
# Author: Dilshan Angampitiya
#         Steven Bird (revisions)
# Date:   24/1/2008

# Brief description of the Module# define custom exceptions
# use exceptions for all errors found in testing

import sys, copy
import types

from ivle import testfilespace

# Don't let nose into here, as it has lots of stuff named Test* without being
# tests.
__test__ = False

# student error or author error
# errors in student code get handled internally
# errors in solution code get passed up
class ScriptExecutionError(Exception):
    """Runtime error in the student code or solution code"""
    def __init__(self, exc_info):
        cla, exc, trbk = exc_info
        self._name = cla.__name__
        self._detail = str(exc)
        self._trbk = trbk

    def is_critical(self):
        if (    self._name == 'FunctionNotFoundError'
            or  self._name == 'SyntaxError'
            or  self._name == 'IndentationError'):
            return True
        else:
            return False

    def to_dict(self):
        import traceback
        return {'name': self._name,
                'detail': self._detail,
                'critical': self.is_critical(),
                'lineno': traceback.tb_lineno(self._trbk)
                }

    def __str__(self):
        return self._name + " - " + str(self._detail)

# author error
class TestCreationError(Exception):
    """An error occured while creating the test suite or one of its components"""
    def __init__(self, reason):
        self._reason = reason
        
    def __str__(self):
        return self._reason

# author error
class TestError(Exception):
    """Runtime error in the testing framework outside of the provided or student code"""
    def __init__(self, exc_info):
        cla, exc, trbk = exc_info
        self._name = cla.__name__
        self._detail = str(exc)
        self._exc_info = exc_info

    def exc_info(self):
        return self._exc_info

    def __str__(self):
        return "Error testing solution against attempt: %s - %s" %(self._name, self._detail)

# author error
# raised when expected file not found in solution output
# Always gets caught and passed up as a TestError
class FileNotFoundError(Exception):
    def __init__(self, filename):
        self._filename = filename

    def __str__(self):
        return "File %s not found in output" %(self._filename)
    

# Error encountered when executing solution or attempt code
# Always gets caught and passed up in a ScriptExecutionError
class FunctionNotFoundError(Exception):
    """This error is returned when a function was expected in a
    test case but was not found"""
    def __init__(self, function_name):
        self.function_name = function_name

    def __str__(self):
        return "Function " + self.function_name + " not found"

class TestCasePart:
    """
    A part of a test case which compares a subset of the input files or file streams.
    This can be done either with a comparison function, or by comparing directly, after
    applying normalisations.
    """

    ident = classmethod(lambda x: x)
    ignore = classmethod(lambda x: None)
    match = classmethod(lambda x,y: x==y)
    always_match = classmethod(lambda x,y: True)
    true = classmethod(lambda *x: True)
    false = classmethod(lambda *x: False)

    def __init__(self, test_case):
        """Initialise with descriptions (pass,fail) and a default behavior for output
        If default is match, unspecified files are matched exactly
        If default is ignore, unspecified files are ignored
        The default default is match.
        """
        self._pass_msg = test_case.passmsg
        self._fail_msg = test_case.failmsg
        self._default = test_case.test_default
        if self._default == 'ignore':
            self._default_func = self.true
        else:
            self._default_func = self.match

        self._file_tests = {}
        self._stdout_test = ('check', self._default_func)
        self._stderr_test = ('check', self._default_func)
        self._exception_test = ('check', self._default_func)
        self._result_test = ('check', self._default_func)
        self._code_test = ('check', self._default_func)
        
        for part in test_case.parts:
            if part.part_type =="file":
                self.add_file_test(part)
            elif part.part_type =="stdout":
                self.add_stdout_test(part)
            elif part.part_type =="stderr":
                self.add_stderr_test(part)
            elif part.part_type =="result":
                self.add_result_test(part)
            elif part.part_type =="exception":
                self.add_exception_test(part)
            elif part.part_type =="code":
                self.add_code_test(part)

    def _set_default_function(self, function, test_type):
        """"Ensure test type is valid and set function to a default
        if not specified"""
        
        if test_type not in ['norm', 'check']:
            raise TestCreationError("Invalid test type in %s" %self._desc)
        
        if function == '':
            if test_type == 'norm': function = self.ident
            else: function = self.match

        return function

    def _validate_function(self, function, included_code):
        """Create a function object from the given string.
        If a valid function object cannot be created, raise an error.
        """
        if not callable(function):
            try:
                exec "__f__ = %s" %function in included_code
            except:
                raise TestCreationError("Invalid function %s" % function)

            f = included_code['__f__']

            if not callable(f):
                raise TestCreationError("Invalid function %s" % function)
        else:
            f = function

        return f

    def validate_functions(self, included_code):
        """Ensure all functions used by the test cases exist and are callable.
        Also convert their string representations to function objects.
        This can only be done once all the include code has been specified.
        """
        (test_type, function) = self._stdout_test
        self._stdout_test = (test_type, self._validate_function(function, included_code))
        
        (test_type, function) = self._stderr_test
        self._stderr_test = (test_type, self._validate_function(function, included_code))
        
        (test_type, function) = self._result_test
        self._result_test = (test_type, self._validate_function(function, included_code))
        
        (test_type, function) = self._exception_test
        self._exception_test = (test_type, self._validate_function(function, included_code))

        for filename, (test_type, function) in self._file_tests.items():
            self._file_tests[filename] = (test_type, self._validate_function(function, included_code))
            
    def add_result_test(self, part):
        "Test part that compares function return values"
        function = self._set_default_function(part.data, part.test_type)
        self._result_test = (part.test_type, function)
            
    def add_stdout_test(self, part):
        "Test part that compares stdout"
        function = self._set_default_function(part.data, part.test_type)
        self._stdout_test = (part.test_type, function)

    def add_stderr_test(self, part):
        "Test part that compares stderr"
        function = self._set_default_function(part.data, part.test_type)
        self._stderr_test = (part.test_type, function)

    def add_exception_test(self, part):
        "Test part that compares stderr"
        function = self._set_default_function(part.data, part.test_type)
        self._exception_test = (part.test_type, function)

    def add_file_test(self, part):
        "Test part that compares the contents of a specified file"
        function = self._set_default_function(part.data, part.test_type)
        self._file_tests[part.filename] = (part.test_type, function)

    def add_code_test(self, part):
        "Test part that examines the supplied code"
        function = self._set_default_function(part.data, part.test_type)
        self._code_test = (part.test_type, function)

    def _check_output(self, solution_output, attempt_output, test_type, f):
        """Compare solution output and attempt output using the
        specified comparison function.
        """
        solution_output = str(solution_output)
        attempt_output = str(attempt_output)
            
        if test_type == 'norm':
            return f(solution_output) == f(attempt_output)
        else:
            return f(solution_output, attempt_output)

    def _check_code(self, solution, attempt, test_type, f, include_space):
        """Compare solution code and attempt code using the
        specified comparison function.
        """
        if type(f) in types.StringTypes:  # kludge
            f = eval(str(f), include_space)
        if test_type == 'norm':
            return f(solution) == f(attempt)
        else:
            return f(solution, attempt)

    def run(self, solution_data, attempt_data, include_space):
        """Run the tests to compare the solution and attempt data
        Returns the empty string if the test passes, or else an error message.
        """

        # check source code itself
        (test_type, f) = self._code_test
        if not self._check_code(solution_data['code'], attempt_data['code'], test_type, f, include_space):       
            return 'Unexpected code'

        # check function return value (None for scripts)
        (test_type, f) = self._result_test
        if not self._check_output(solution_data['result'], attempt_data['result'], test_type, f):
            return 'Unexpected function return value'

        # check stdout
        (test_type, f) = self._stdout_test
        if not self._check_output(solution_data['stdout'], attempt_data['stdout'], test_type, f):
            return 'Unexpected output'

        #check stderr
        (test_type, f) = self._stderr_test
        if not self._check_output(solution_data['stderr'], attempt_data['stderr'], test_type, f):
            return 'Unexpected error output'

        #check exception
        (test_type, f) = self._exception_test
        if not self._check_output(solution_data['exception'], attempt_data['exception'], test_type, f):
            return 'Unexpected exception'

        solution_files = solution_data['modified_files']
        attempt_files = attempt_data['modified_files']

        # check files indicated by test
        for (filename, (test_type, f)) in self._file_tests.items():
            if filename not in solution_files:
                raise FileNotFoundError(filename)
            elif filename not in attempt_files:
                return filename + ' not found'
            elif not self._check_output(solution_files[filename], attempt_files[filename], test_type, f):
                return filename + ' does not match'

        if self._default == 'ignore':
            return ''

        # check files found in solution, but not indicated by test
        for filename in [f for f in solution_files if f not in self._file_tests]:
            if filename not in attempt_files:
                return filename + ' not found'
            elif not self._check_output(solution_files[filename], attempt_files[filename], 'match', self.match):
                return filename + ' does not match'

        # check if attempt has any extra files
        for filename in [f for f in attempt_files if f not in solution_files]:
            return "Unexpected file found: " + filename

        # Everything passed with no problems
        return ''
        
class TestCase:
    """
    A set of tests with a common inputs
    """
    def __init__(self, console, suite):
        """Initialise with name and optionally, a function to test (instead of the entire script)
        The inputs stdin, the filespace and global variables can also be specified at
        initialisation, but may also be set later.
        """
        self._console = console
        self._name = suite.description
        
        function = suite.function
        if function == '': function = None
        self._function = function
        self._list_args = []
        self._keyword_args = {}
        
        self.set_stdin(suite.stdin)
        self._filespace = testfilespace.TestFilespace(None)
        self._global_space = {}
        self._parts = []
        self._allowed_exceptions = set()
        
        args = {}
        for var in suite.variables:
            if var.var_type == "file":
                self.add_file(var)
            elif var.var_type == "var":
                self.add_variable(var)
            elif var.var_type == "arg":
                args[var.arg_no] = var
            elif var.var_type == "exception":
                self.add_exception(var)
        
        for i in xrange(len(args)):
            self.add_arg(args[i])
        for test_case in suite.test_cases:
            self.add_part(TestCasePart(test_case))

    def set_stdin(self, stdin):
        """ Set the given string as the stdin for this test case"""
        # stdin must have a newline at the end for raw_input to work properly
        if stdin is not None:
            if stdin[-1:] != '\n':
                stdin += '\n'
        else:
            stdin = ""
        self._stdin = stdin

    def add_file(self, filevar):
        """ Insert the given filename-data pair into the filespace for this test case"""
        # TODO: Add the file to the console
        self._filespace.add_file(filevar.var_name, "")
        
    def add_variable(self, var):
        """ Add the given varibale-value pair to the initial global environment
        for this test case. The value is the string repr() of an actual value.
        Throw an exception if the value cannot be paresed.
        """
        
        try:
            self._global_space[var.var_name] = eval(var.var_value)
        except:
            raise TestCreationError("Invalid value for variable %s: %s" 
                                    %(var.var_name, var.var_value))

    def add_arg(self, var):
        """ Add a value to the argument list. This only applies when testing functions.
        By default arguments are not named, but if they are, they become keyword arguments.
        """
        try:
            if var.var_name == None or var.var_name == '':
                self._list_args.append(eval(var.var_value))
            else:
                self._keyword_args[var.var_name] = var.var_value
        except:
            raise TestCreationError("Invalid value for function argument: %s" %var.var_value)

    def add_exception(self, exception_name):
        self._allowed_exceptions.add(var.var_name)
        
    def add_part(self, test_part):
        """ Add a TestPart to this test case"""
        self._parts.append(test_part)

    def validate_functions(self, included_code):
        """ Validate all the functions in each part in this test case
        This can only be done once all the include code has been specified.
        """
        for part in self._parts:
            part.validate_functions(included_code)

    def get_name(self):
        """ Get the name of the test case """
        return self._name

    def run(self, solution, attempt_code, include_space, stop_on_fail=True):
        """ Run the solution and the attempt with the inputs specified for this test case.
        Then pass the outputs to each test part and collate the results.
        """
        case_dict = {}
        case_dict['name'] = self._name
        
        # Run solution
        try:
            global_space_copy = copy.deepcopy(self._global_space)
            solution_data = self._execstring(solution, global_space_copy)
            self._console.stdin.truncate(0)
            self._console.stdin.write(self._stdin)
            
            # if we are just testing a function
            if not self._function == None:
                if self._function not in solution_data['globals']:
                    raise FunctionNotFoundError(self._function)
                solution_data = self._run_function(self._function,
                    self._list_args, self._keyword_args, solution)
                
        except Exception, e:
            raise e #ScriptExecutionError(sys.exc_info())

        # Run student attempt
        try:
            global_space_copy = copy.deepcopy(self._global_space)
            attempt_data = self._execstring(attempt_code, global_space_copy)
            self._console.stdin.truncate(0)
            self._console.stdin.write(self._stdin)
            
            # if we are just testing a function
            if not self._function == None:
                if self._function not in attempt_data['globals']:
                    raise FunctionNotFoundError(self._function)
                attempt_data = self._run_function(self._function,
                    self._list_args, self._keyword_args, attempt_code)
        except:
            case_dict['exception'] = ScriptExecutionError(sys.exc_info()).to_dict()
            case_dict['passed'] = False
            return case_dict
        
        results = []
        passed = True
        
        # generate results
        for test_part in self._parts:
            try:
                result = test_part.run(solution_data, attempt_data, include_space)
            except:
                raise TestError(sys.exc_info())
            
            result_dict = {}
            result_dict['description'] = test_part._pass_msg
            result_dict['passed'] = (result == '')
            if result_dict['passed'] == False:
                result_dict['error_message'] = result
                result_dict['description'] = test_part._fail_msg
                passed = False
                
            results.append(result_dict)

            # Do we continue the test_parts after one of them has failed?
            if not passed and stop_on_fail:
                break;

        case_dict['parts'] = results
        case_dict['passed'] = passed

        return case_dict
                
    def _execfile(self, filename, global_space):
        """ Execute the file given by 'filename' in global_space, and return the outputs. """
        self._initialise_global_space(global_space)
        data = self._run_function(lambda: execfile(filename, global_space),
            code = open(filename).read())
        return data

    def _execstring(self, string, global_space):
        """ Execute the given string in global_space, and return the outputs. 
        """
        self._initialise_global_space(global_space)
        
        inspection = self._console.execute(string)

        exception_name = None
        if 'exception' in inspection:
            exception = inspection['exception']['except']
            exception_name = type(exception).__name__
            raise(exception)

        return {'code': string,
                'result': None,
                'globals': self._console.globals(),
                'exception': exception_name, # Hmmm... odd? Is this right?
                'stdout': self._console.stdout.read(),
                'stderr': self._console.stderr.read(),
                'modified_files': None}

    def _initialise_global_space(self, global_space):
        """ Modify the provided global_space so that file, open and raw_input are redefined
        to use our methods instead.
        """
        self._console.globals(global_space)
        self._current_filespace_copy = self._filespace.copy()
        global_space['file'] = lambda filename, mode='r', bufsize=-1: self._current_filespace_copy.openfile(filename, mode)
        global_space['open'] = global_space['file']
        global_space['raw_input'] = lambda x=None: raw_input()
        return global_space

    def _run_function(self, function, args, kwargs, code):
        """ Run the provided function with the provided stdin, capturing stdout and stderr
        and the return value.
        Return all the output data.
        code: The full text of the code, which needs to be stored as part of
        the returned dictionary.
        """
        s_args = map(repr, args)
        s_kwargs = dict(zip(kwargs.keys(), map(repr, kwargs.values())))
        call = self._console.call(function, *s_args, **s_kwargs)

        exception_name = None
        if 'exception' in call:
            exception = call['exception']['except']
            exception_name = type(exception).__name__
            raise(exception)

        return {'code': code,
                'result': call['result'],
                'exception': exception_name,
                'stdout': self._console.stdout.read(),
                'stderr': self._console.stderr.read(),
                'modified_files': None}

class TestSuite:
    """
    The complete collection of test cases for a given exercise
    """
    def __init__(self, exercise, console):
        """Initialise with the name of the test suite (the exercise name) and the solution.
        The solution may be specified later.
        """
        self._solution = exercise.solution
        self._name = exercise.id
        self._exercise = exercise
        self._tests = []
        self._console = console
        self.add_include_code(exercise.include)
        
        for test_case in exercise.test_suites:
            new_case = TestCase(console, test_case)
            self.add_case(new_case)

    def has_solution(self):
        " Returns true if a solution has been provided "
        return self._solution != None

    def add_include_code(self, include_code = ''):
        """ Add include code that may be used by the test cases during
        comparison of outputs.
        """
        
        # if empty, make sure it can still be executed
        if include_code == "" or include_code is None:
            include_code = "pass"
        self._include_code = include_code
        
        include_space = {}
        try:
            exec self._include_code in include_space
        except:
            raise TestCreationError("-= Bad include code =-\n" + include_code)

        self._include_space = include_space

    def add_case(self, test_case):
        """ Add a TestCase, then validate all functions inside test case
        now that the include code is known
        """
        self._tests.append(test_case)
        test_case.validate_functions(self._include_space)

    def run_tests(self, attempt_code, stop_on_fail=False):
        " Run all test cases on the specified console and collate the results "
        
        exercise_dict = {}
        exercise_dict['name'] = self._name
        
        test_case_results = []
        passed = True
        for test in self._tests:
            result_dict = test.run(self._solution, attempt_code, self._include_space)
            if 'exception' in result_dict and result_dict['exception']['critical']:
                # critical error occured, running more cases is useless
                # FunctionNotFound, Syntax, Indentation
                exercise_dict['critical_error'] = result_dict['exception']
                exercise_dict['passed'] = False
                return exercise_dict
            
            test_case_results.append(result_dict)
            
            if not result_dict['passed']:
                passed = False
                if stop_on_fail:
                    break

        exercise_dict['cases'] = test_case_results
        exercise_dict['passed'] = passed
        return exercise_dict

    def get_name(self):
        return self._names  
