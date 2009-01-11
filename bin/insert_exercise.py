
import os
import pg
import sys

from common import db

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print >> sys.stderr, "usage: %s filename ..." % sys.argv[0]
        print >> sys.stderr, "  insert the given filenames as exercises"
        sys.exit(1)

    conn = db.DB()
    for fname in sys.argv[1:]:
        if not os.access(fname, os.R_OK):
            print >> sys.stderr, "No permission to read %s" % fname
            continue
        spec = open(fname, "r").read()

        fields = {'identifier':fname, 'spec':spec}
        
        try:
            conn.insert(fields, 'problem', ['identifier', 'spec'])
        except Exception, e:
            print >> sys.stderr, "error inserting %s: %s" % (fname, repr(e))
                    
