#!/usr/bin/python

import sys

if __name__ == "__main__":
    inf = open(sys.argv[1], "rb")
    sys.stdout.write(inf.read())
    inf.close()
