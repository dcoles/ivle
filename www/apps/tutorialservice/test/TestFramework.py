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
# Date:   24/1/2008

# Brief description of the Module# define custom exceptions
# use exceptions for all errors found in testing

import sys, StringIO, copy

# author error
class TestCreationError(Exception):
    """An error occured while creating the test suite or one of its components"""
    def __init__(self, reason):
        self._reason = reason
        
    def __str__(self):
        return self._reason

# author error
class SolutionError(Exception):
    """Error in the provided solution"""
    def __init__(self, exc_info):
        cla, exc, trbk = exc_info
        self.name = cla.__name__
        self._detail = str(exc)
        self._exc_info = exc_info

    def to_dict(self):
        return {'name': self._name,
                'detail': self._detail
                'critical': False
                }

    def exc_info(self):
        return self._exc_info

    def __str__(self):
        return "Error running solution: %s" %str(self._detail)

# author error
class TestError(Exception):
    """Runtime error in the testing framework outside of the provided or student code"""
    def __init__(self, exc_info):
        cla, exc, trbk = exc_info
        self.name = cla.__name__
        self._detail = str(exc)
        self._exc_info = exc_info

    def exc_info(self):
        return self._exc_info

    def __str__(self):
        return "Error testing solution against attempt: %s" %str(self._detail)

# student error
class AttemptError(Exception):
    """Runtime error in the student code"""
    def __init__(self, exc_info):
        cla, exc, trbk = exc_info
        self._name = cla.__name__
        self._detail = str(exc)

    def is_critical(self):
        if (    self._name == 'FunctionNotFoundError'
            or  self._name == 'SyntaxError'
            or  self._name == 'IndentationError'):
            return True
        else:
            return False

    def to_dict(self):
        return {'name': self._name,
                'detail': self._detail,
                'critical': self.is_critical()
                }

    def __str__(self):
        return self._name + " - " + str(self._detail)

# student error
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
    This can be done either with a comparision function, or by comparing directly, after
    applying normalisations.
    """
    # how to make this work? atm they seem to get passed the class as a first arg
    ident =lambda x: x
    ignore = lambda x: None
    match = lambda x,y: x==y
    always_match = lambda x,y: True
    true = lambda *x: True
    false = lambda *x: False

    def __init__(self, desc, default='match'):
        """Initialise with a description and a default behavior for output
        If default is match, unspecified files are matched exactly
        If default is ignore, unspecified files are ignored
        The default default is match.
        """
        self._desc = desc
        self._default = default
        if default == 'ignore':
            self._default_func = lambda *x: True
        else:
            self._default_func = lambda x,y: x==y

        self._file_tests = {}
        self._stdout_test = ('check', self._default_func)
        self._stderr_test = ('check', self._default_func)
        self._exception_test = ('check', self._default_func)
        self._result_test = ('check', self._default_func)

    def get_description(self):
        "Getter for description"
        return self._desc

    def _set_default_function(self, function, test_type):
        """"Ensure test type is valid and set function to a default
        if not specified"""
        
        if test_type not in ['norm', 'check']:
            raise TestCreationError("Invalid test type in %s" %self._desc)
        
        if function == '':
            if test_type == 'norm': function = lambda x: x
            else: function = lambda x,y: x==y

        return function

    def _validate_function(self, function, included_code):
        """Create a function object from the given string.
        If a valid function object cannot be created, raise and error.
        """
        if not callable(function):
            try:
                exec "__f__ = %s" %function in included_code
            except:
                raise TestCreationError("Invalid function %s" %function)

            f = included_code['__f__']

            if not callable(f):
                raise TestCreationError("Invalid function %s" %function)    
        else:
            f = function

        return f

    def validate_functions(self, included_code):
        """Ensure all functions used by the test cases exist and are callable.
        Also covert their string representations to function objects.
        This can only be done once all the include code has been specified.
        """
        (test_type, function) = self._stdout_test
        self._stdout_test = (test_type, self._validate_function(function, included_code))
        
        (test_type, function) = self._stderr_test
        self._stderr_test = (test_type, self._validate_function(function, included_code))

        for filename, (test_type, function) in self._file_tests.items():
            self._file_tests[filename] = (test_type, self._validate_function(function, included_code))
            
    def add_result_test(self, function, test_type='norm'):
        "Test part that compares function return values"
        function = self._set_default_function(function, test_type)
        self._result_test = (test_type, function)

            
    def add_stdout_test(self, function, test_type='norm'):
        "Test part that compares stdout"
        function = self._set_default_function(function, test_type)
        self._stdout_test = (test_type, function)
        

    def add_stderr_test(self, function, test_type='norm'):
        "Test part that compares stderr"
        function = self._set_default_function(function, test_type)
        self._stderr_test = (test_type, function)

    def add_exception_test(self, function, test_type='norm'):
        "Test part that compares stderr"
        function = self._set_default_function(function, test_type)
        self._exception_test = (test_type, function)

    def add_file_test(self, filename, function, test_type='norm'):
        "Test part that compares the contents of a specified file"
        function = self._set_default_function(function, test_type)
        self._file_tests[filename] = (test_type, function)

    def _check_output(self, solution_output, attempt_output, test_type, f):
        """Compare solution output and attempt output using the
        specified comparision function.
        """
        # converts unicode to string
        if type(solution_output) == unicode:    
            solution_output = str(solution_output)
            
        if type(attempt_output) == unicode:
            attempt_output = str(attempt_output)
            
        if test_type == 'norm':
            return f(solution_output) == f(attempt_output)
        else:
            return f(solution_output, attempt_output)

    def run(self, solution_data, attempt_data):
        """Run the tests to compare the solution and attempt data
        Returns the empty string is the test passes, or else an error message.
        """

        # check function return value (None for scripts)
        (test_type, f) = self._result_test
        if not self._check_output(solution_data['result'], attempt_data['result'], test_type, f):       
            return 'function return value does not match'

        # check stdout
        (test_type, f) = self._stdout_test
        if not self._check_output(solution_data['stdout'], attempt_data['stdout'], test_type, f):       
            return 'stdout does not match'

        #check stderr
        (test_type, f) = self._stderr_test
        if not self._check_output(solution_data['stderr'], attempt_data['stderr'], test_type, f):        
            return 'stderr does not match'

        #check exception
        (test_type, f) = self._exception_test
        if not self._check_output(solution_data['exception'], attempt_data['exception'], test_type, f):        
            return 'exception does not match'


        solution_files = solution_data['modified_files']
        attempt_files = attempt_data['modified_files']

        # check files indicated by test
        for (filename, (test_type, f)) in self._file_tests.items():
            if filename not in solution_files:
                raise SolutionError('File %s not found' %filename)
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
            elif not self._check_output(solution_files[filename], attempt_files[filename], 'match', lambda x,y: x==y):
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
    def __init__(self, name='', function=None, stdin='', filespace=None, global_space=None):
        """Initialise with name and optionally, a function to test (instead of the entire script)
        The inputs stdin, the filespace and global variables can also be specified at
        initialisation, but may also be set later.
        """
        if global_space == None:
            global_space = {}
        if filespace == None:
            filespace = {}
        
        self._name = name
        
        if function == '': function = None
        self._function = function
        self._list_args = []
        self._keyword_args = {}
        
        # stdin must have a newline at the end for raw_input to work properly
        if stdin[-1:] != '\n': stdin += '\n'
        
        self._stdin = stdin
        self._filespace = TestFilespace(filespace)
        self._global_space = global_space
        self._parts = []
        self._allowed_exceptions = set()

    def set_stdin(self, stdin):
        """ Set the given string as the stdin for this test case"""
        self._stdin = stdin

    def add_file(self, filename, data):
        """ Insert the given filename-data pair into the filespace for this test case"""
        self._filespace.add_file(filename, data)
        
    def add_variable(self, variable, value):
        """ Add the given varibale-value pair to the initial global environment
        for this test case.
        Throw and exception if thevalue cannot be paresed.
        """
        
        try:
            self._global_space[variable] = eval(value)
        except:
            raise TestCreationError("Invalid value for variable %s: %s" %(variable, value))

    def add_arg(self, value, name=None):
        """ Add a value to the argument list. This only applies when testing functions.
        By default arguments are not named, but if they are, they become keyword arguments.
        """
        try:
            if name == None or name == '':
                self._list_args.append(eval(value))
            else:
                self._keyword_args[name] = value
        except:
            raise TestCreationError("Invalid value for function argument: %s" %value)

    def add_exception(self, exception_name):
        self._allowed_exceptions.add(exception_name)
        
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

    def run(self, solution, attempt_code):
        """ Run the solution and the attempt with the inputs specified for this test case.
        Then pass the outputs to each test part and collate the results.
        """
        case_dict = {}
        case_dict['name'] = self._name
        
        # Run solution
        try:
            global_space_copy = copy.deepcopy(self._global_space)
            solution_data = self._execstring(solution, global_space_copy)
            
            # if we are just testing a function
            if not self._function == None:
                if self._function not in global_space_copy:
                    raise FunctionNotFoundError(self._function)
                solution_data = self._run_function(lambda: global_space_copy[self._function](*self._list_args, **self._keyword_args))
                
        except:
            raise SolutionError(sys.exc_info())

        # Run student attempt
        try:
            global_space_copy = copy.deepcopy(self._global_space)
            attempt_data = self._execstring(attempt_code, global_space_copy)
            
            # if we are just testing a function
            if not self._function == None:
                if self._function not in global_space_copy:
                    raise FunctionNotFoundError(self._function)
                attempt_data = self._run_function(lambda: global_space_copy[self._function](*self._list_args, **self._keyword_args))
        except:
            case_dict['exception'] = AttemptError(sys.exc_info()).to_dict()
            case_dict['passed'] = False
            return case_dict
        
        results = []
        passed = True
        
        # generate results
        for test_part in self._parts:
            result = test_part.run(solution_data, attempt_data)
            result_dict = {}
            result_dict['description'] = test_part.get_description()
            result_dict['passed']  = (result == '')
            if result_dict['passed'] == False:
                result_dict['error_message'] = result
                passed = False
                
            results.append(result_dict)

        case_dict['parts'] = results
        case_dict['passed'] = passed

        return case_dict
                
    def _execfile(self, filename, global_space):
        """ Execute the file given by 'filename' in global_space, and return the outputs. """
        self._initialise_global_space(global_space)
        data = self._run_function(lambda: execfile(filename, global_space))
        return data

    def _execstring(self, string, global_space):
        """ Execute the given string in global_space, and return the outputs. """
        self._initialise_global_space(global_space)
        # _run_function handles tuples in a special way
        data = self._run_function((string, global_space))
        return data

    def _initialise_global_space(self, global_space):
        """ Modify the provided global_space so that file, open and raw_input are redefined
        to use our methods instead.
        """
        self._current_filespace_copy = self._filespace.copy()
        global_space['file'] = lambda filename, mode='r', bufsize=-1: self._current_filespace_copy.openfile(filename, mode)
        global_space['open'] = global_space['file']
        global_space['raw_input'] = lambda x=None: raw_input()
        return global_space

    def _run_function(self, function):
        """ Run the provided function with the provided stdin, capturing stdout and stderr
        and the return value.
        Return all the output data.
        """
        import sys, StringIO
        sys_stdout, sys_stdin, sys_stderr = sys.stdout, sys.stdin, sys.stderr

        output_stream, input_stream, error_stream = StringIO.StringIO(), StringIO.StringIO(self._stdin), StringIO.StringIO()
        sys.stdout, sys.stdin, sys.stderr = output_stream, input_stream, error_stream

        result = None
        exception_name = None
        
        try:
            if type(function) == tuple:
                # very hackish... exec can't be put into a lambda function!
                # or even with eval
                exec(function[0], function[1])
            else:
                result = function()
        except:
            sys.stdout, sys.stdin, sys.stderr = sys_stdout, sys_stdin, sys_stderr
            exception_name = sys.exc_info()[0].__name__
            if exception_name not in self._allowed_exceptions:
                raise
        
        sys.stdout, sys.stdin, sys.stderr = sys_stdout, sys_stdin, sys_stderr

        self._current_filespace_copy.flush_all()
            
        return {'result': result,
                'exception': exception_name,
                'stdout': output_stream.getvalue(),
                'stderr': output_stream.getvalue(),
                'modified_files': self._current_filespace_copy.get_modified_files()}

class TestSuite:
    """
    The complete collection of test cases for a given problem
    """
    def __init__(self, name, solution=None):
        """Initialise with the name of the test suite (the problem name) and the solution.
        The solution may be specified later.
        """
        self._solution = solution
        self._name = name
        self._tests = []
        self.add_include_code("")

    def add_solution(self, solution):
        " Specifiy the solution script for this problem "
        self._solution = solution

    def has_solution(self):
        " Returns true if a soltion has been provided "
        return self._solution != None

    def add_include_code(self, include_code = ''):
        """ Add include code that may be used by the test cases during
        comparison of outputs.
        """
        
        # if empty, make sure it can still be executed
        if include_code == "":
            include_code = "pass"
        self._include_code = str(include_code)
        
        include_space = {}
        try:
            exec self._include_code in include_space
        except:
            raise TestCreationError("Bad include code")

        self._include_space = include_space
    
    def add_case(self, test_case):
        """ Add a TestCase, then validate all functions inside test case
        now that the include code is known
        """
        self._tests.append(test_case)
        test_case.validate_functions(self._include_space)

    def run_tests(self, attempt_code, stop_on_fail=True):
        " Run all test cases and collate the results "
        
        problem_dict = {}
        problem_dict['name'] = self._name
        
        test_case_results = []
        for test in self._tests:
            result_dict = test.run(self._solution, attempt_code)
            if 'exception' in result_dict and result_dict['exception']['critical']:
                # critical error occured, running more cases is useless
                # FunctionNotFound, Syntax, Indentation
                problem_dict['critical_error'] = result_dict['exception']
                return problem_dict
            
            test_case_results.append(result_dict)
            
            if not result_dict['passed'] and stop_on_fail:
                break

        problem_dict['cases'] = test_case_results
        return problem_dict

    def get_name(self):
        return self._name

class TestFilespace:
    """
    Our dummy file system which is accessed by code being tested.
    Implemented as a dictionary which maps filenames to strings
    """
    def __init__(self, files=None):
        "Initialise, optionally with filename-filedata pairs"

        if files == None:
            files = {}

        # dict mapping files to strings
        self._files = {}
        self._files.update(files)
        # set of file names
        self._modified_files = set([])
        # dict mapping files to stringIO objects
        self._open_files = {}

    def add_file(self, filename, data):
        " Add a file to the filespace "
        self._files[filename] = data

    def openfile(self, filename, mode='r'):
        """ Open a file from the filespace with the given mode.
        Return a StringIO subclass object with the file contents.
        """
        import re

        if filename in self._open_files:
            raise IOError("File already open: %s" %filename)

        if not re.compile("[rwa][+b]{0,2}").match(mode):
            raise IOError("invalid mode %s" %mode)
        
        ## TODO: validate filename?
        
        mode.replace("b",'')
        
        # initialise the file properly (truncate/create if required)
        if mode[0] == 'w':
            self._files[filename] = ''
            self._modified_files.add(filename)
        elif filename not in self._files:
            if mode[0] == 'a':
                self._files[filename] = ''
                self._modified_files.add(filename)
            else:
                raise IOError(2, "Access to file denied: %s" %filename)

        # for append mode, remember the existing data
        if mode[0] == 'a':
            existing_data = self._files[filename]
        else:
            existing_data = ""

        # determine what operations are allowed
        reading_ok = (len(mode) == 2 or mode[0] == 'r')
        writing_ok = (len(mode) == 2 or mode[0] in 'wa')

        # for all writing modes, start off with blank file
        if mode[0] == 'w':
            initial_data = ''
        else:
            initial_data = self._files[filename]

        file_object = TestStringIO(initial_data, filename, self, reading_ok, writing_ok, existing_data)
        self._open_files[filename] = file_object
        
        return file_object

    def flush_all(self):
        """ Flush all open files
        """
        for file_object in self._open_files.values():
            file_object.flush()

    def updatefile(self,filename, data):
        """ Callback function used by an open file to inform when it has been updated.
        """
        if filename in self._open_files:
            self._files[filename] = data
            if self._open_files[filename].is_modified():
                self._modified_files.add(filename)
        else:
            raise IOError(2, "Access to file denied: %s" %filename)

    def closefile(self, filename):
        """ Callback function used by an open file to inform when it has been closed.
        """
        if filename in self._open_files:
            del self._open_files[filename]

    def get_modified_files(self):
        """" A subset of the filespace containing only those files which have been
        modified
        """
        modified_files = {}
        for filename in self._modified_files:
            modified_files[filename] = self._files[filename]

        return modified_files

    def get_open_files(self):
        " Return the names of all open files "
        return self._open_files.keys()
            
    def copy(self):
        """ Return a copy of the current filespace.
        Only the files are copied, not the modified or open file lists.
        """
        self.flush_all()
        return TestFilespace(self._files)

class TestStringIO(StringIO.StringIO):
    """
    A subclass of StringIO which acts as a file in our dummy file system
    """
    def __init__(self, string, filename, filespace, reading_ok, writing_ok, existing_data):
        """ Initialise with the filedata, file name and infomation on what ops are
        acceptable """
        StringIO.StringIO.__init__(self, string)
        self._filename = filename
        self._filespace = filespace
        self._reading_ok = reading_ok
        self._writing_ok = writing_ok
        self._existing_data = existing_data
        self._modified = False
        self._open = True

    # Override all standard file ops. Make sure that they are valid with the given
    # permissions and if so then call the corresponding method in StringIO
    
    def read(self, *args):
        if not self._reading_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.read(self, *args)

    def readline(self, *args):
        if not self._reading_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.readline(self, *args)

    def readlines(self, *args):
        if not self._reading_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.readlines(self, *args)

    def seek(self, *args):
        if not self._reading_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.seek(self, *args)

    def truncate(self, *args):
        self._modified = True
        if not self._writing_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.truncate(self, *args)
        
    def write(self, *args):
        self._modified = True
        if not self._writing_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.write(self, *args)

    def writelines(self, *args):
        self._modified = True
        if not self._writing_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.writelines(self, *args)

    def is_modified(self):
        " Return true if the file has been written to, or truncated"
        return self._modified
        
    def flush(self):
        " Update the contents of the filespace with the new data "
        self._filespace.updatefile(self._filename, self._existing_data+self.getvalue())
        return StringIO.StringIO.flush(self)

    def close(self):
        " Flush the file and close it "
        self.flush()
        self._filespace.closefile(self._filename)
        return StringIO.StringIO.close(self)

##def get_function(filename, function_name):
##	import compiler
##	mod = compiler.parseFile(filename)
##	for node in mod.node.nodes:
##		if isinstance(node, compiler.ast.Function) and node.name == function_name:
##			return node
##  
