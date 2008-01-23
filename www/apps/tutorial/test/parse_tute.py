from xml.dom.minidom import *
from TestFramework import *

DEFAULT_TEST_TYPE = 'norm'
DEFAULT_CASE_TYPE = 'match'

class ParseException(Exception):
    " Error when parsing the xml problem file "
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
    """ Create an TestCasePaart instance from test part xml data
    """
    
    func_desc = partNode.getAttribute('desc')
    default = partNode.getAttribute('default')
    if default == '': default = DEFAULT_CASE_TYPE
    
    part = TestCasePart(func_desc, default)

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
        elif child.tagName == 'file':
            test_type = child.getAttribute('type')
            if test_type == '': test_type = DEFAULT_TEST_TYPE
            filename = child.getAttribute('name')
            if filename == '':
                raise ParseException("File without name in case %s" %case_name)
            part.add_file_test(filename, getTextData(child), test_type)

    return part

def getCaseData(caseNode):
    """ Creare a TestCase instance from test case xml data
    """
    
    case_name = caseNode.getAttribute('name')
    function = caseNode.getAttribute('function')
    if function == '': function = None
    case = TestCase(case_name, function)
    
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
        elif child.tagName == 'function':
            # specify a test case part
            case.add_part(getCasePartData(child))

    return case
                
def parse_tutorial_file(filename, prob_num=1):
    """ Parse an xml problem file and return a testsuite for that problem """
    dom = parse(filename)

    # get problem
    count = 0
    problem = None
    for child in dom.childNodes:
        if child.nodeType == child.ELEMENT_NODE and child.tagName == 'problem':
            count += 1
            if count == prob_num:
                problem = child
                break

    if problem == None:
        raise ParseException("Not enough problems")

    # get name
    problem_name = problem.getAttribute('name')

    if not problem_name:
        raise ParseException('Problem name not supplied')

    problem_suite = TestSuite(problem_name)

    # get solution and include info
    for child in problem.childNodes:
        if child.nodeType != child.ELEMENT_NODE:
            continue
        if child.tagName == 'solution':
            problem_suite.add_solution(getTextData(child))
        elif child.tagName == 'include':
            problem_suite.add_include_code(getTextData(child))
        elif child.tagName == 'case':
            problem_suite.add_case(getCaseData(child))

    return problem_suite

