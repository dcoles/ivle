#!/usr/bin/python

import sys

if __name__ == "__main__":
    out = open(sys.argv[1], "wb")
    out.write(sys.stdin.read())
    out.close()
