
from parse_tute import *

def print_results((name, results)):
    """ Print the output of a testsuite nicely """
    print name
    for (case_name, test_results) in results:
        print "Case: " + case_name
        for test_result in test_results:
            print "  " + test_result
    print 

problem_suite = parse_exercise_file('all_input_text.xml')
print_results(problem_suite.run_tests("all_input.py"))

problem_suite = parse_exercise_file('fib_text.xml')
print_results(problem_suite.run_tests("fib.py"))
