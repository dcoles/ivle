#!/usr/bin/env python
# Run in a user's jail to test the "short date format" displayed in the
# file browser's file table.
#
# Generates a bunch of files in the current directory and sets their date
# stamps to various dates in the past.
# The files are named after their date stamps relative to today.
#
# Author: Matt Giuca
# Date: 13/1/2008

import os
import time

seconds_per_day = 60*60*24
time_now = time.time()

if time.daylight:
    timezone_offset = time.altzone
else:
    timezone_offset = time.timezone

# Time at the beginning of today, local time
local_daystart \
    = time_now - int(time_now - timezone_offset) % seconds_per_day

def make_file_days_ago(days_ago):
    global time_now
    make_file(str(days_ago) + "days",
        time_now - seconds_per_day*days_ago)
def make_file(fname, timestamp):
    f = open(fname, 'w')
    f.close()
    os.utime(fname, (timestamp, timestamp))

make_file_days_ago(0)
make_file_days_ago(1)
make_file_days_ago(2)
make_file_days_ago(3)
make_file_days_ago(4)
make_file_days_ago(5)
make_file_days_ago(6)
make_file_days_ago(7)
make_file_days_ago(10)
make_file_days_ago(365)

# Now a boundary test - Make a file in the last second of Yesterday.
make_file("first_second_today", local_daystart)
make_file("last_second_yesterday", local_daystart-1)
