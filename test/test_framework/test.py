
import sys
sys.path.append('../../www/apps/tutorial/test/')

from parse_tute import *

def print_results((name, results)):
    """ Print the output of a testsuite nicely """
    print name
    for (case_name, test_results) in results:
        print "Case: " + case_name
        for test_result in test_results:
            print "  " + test_result
    print 

for i in range(1, len(sys.argv)):
    basename = sys.argv[i]
    xmlfile = basename + '_text.xml'
    pyfile = basename + '.py'

    print "Testing:", basename
    problem_suite = parse_tutorial_file(xmlfile)
    print_results(problem_suite.run_tests(pyfile))
