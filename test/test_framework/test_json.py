import sys

try:
    import json
except ImportError:
    import simplejson as json

sys.path.append('../../www/apps/tutorial/test/')

from parse_tute import *

for i in range(1, len(sys.argv)):
    basename = sys.argv[i]
    xmlfile = basename + '_text.xml'
    pyfile = basename + '.py'
    jobj = {"problem": basename}

    problem_suite = parse_exercise_file(xmlfile)
    jobj['name'], results = problem_suite.run_tests(pyfile)
    jobj['cases'] = results

    print json.dumps(jobj)
