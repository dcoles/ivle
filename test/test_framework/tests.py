
import sys
sys.path.append('../../www/apps/tutorialservice/test/')

from parse_tute import *

def print_results(problem):
    print "Problem: %s" %problem['name']
    if 'critical_error' in problem:
        error = problem['critical_error']
        print "Critical error: %s - %s" %(error['name'], error['detail'])
    else:
        for case in problem['cases']:
            print "Case: %s" %case['name']
            if 'exception' in case:
                error = case['exception']
                print "Exception %s - %s" %(error['name'], error['detail'])
            else:
                for part in case['parts']:
                    if part['passed']:
                        print "  Passed: %s" %part['description']
                    else:
                        print "  Failed: %s -- %s" %(part['description'],part['error_message'])
    print
    
problem_suite = parse_tutorial_file('filesum_text.xml')
print_results(problem_suite.run_tests(file("filesum.py").read()))

problem_suite = parse_tutorial_file('hello_text.xml')
print_results(problem_suite.run_tests(file("hello.py").read()))

problem_suite = parse_tutorial_file('all_input_text.xml')
print_results(problem_suite.run_tests(file("all_input.py").read()))

problem_suite = parse_tutorial_file('fib_text.xml')
print_results(problem_suite.run_tests(file("fib.py").read()))
