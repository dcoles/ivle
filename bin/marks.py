#!/usr/bin/env python
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

# Program: Marks
# Author:  Matt Giuca
# Date:    17/4/2008

# Script to calculate the marks for all students for a particular subject.
# Requires root to run.

import conf

import sys
import os
import common.db
import re
import csv
import time
from xml.dom import minidom

if os.getuid() != 0:
    print >>sys.stderr, "Must run marks.py as root."
    sys.exit()

if len(sys.argv) <= 1:
    print >>sys.stderr, "Usage: python ./marks.py subject"
    sys.exit()

# Regex for valid identifiers (subject/worksheet names)
re_ident = re.compile("[0-9A-Za-z_]+")

# This code copy/edited from www/apps/tutorial/__init__.py
def is_valid_subjname(subject):
    m = re_ident.match(subject)
    return m is not None and m.end() == len(subject)

subject = sys.argv[1]

# Subject names must be valid identifiers
if not is_valid_subjname(subject):
    print >>sys.stderr, "Invalid subject name: %s." % repr(subject)
    sys.exit()

def get_userdata(user):
    """
    Given a User object, returns a list of strings for the user data which
    will be part of the output for this user.
    (This is not marks, it's other user data).
    """
    last_login = (None if user.last_login is None else
                    time.strftime("%d/%m/%y", user.last_login))
    return [user.studentid, user.login, user.fullname, last_login]
userdata_header = ["Student ID", "Login", "Full name", "Last login"]

def get_assessable_worksheets(subject):
    """
    Given a subject name, returns a list of strings - the worksheet names (not
    primary key IDs) for all assessable worksheets for that subject.
    May raise Exceptions, which are fatal.
    """
    # NOTE: This code is copy/edited from
    # www/apps/tutorial/__init__.py:handle_subject_menu
    # Should be factored out of there.

    # Parse the subject description file
    # The subject directory must have a file "subject.xml" in it,
    # or it does not exist (raise exception).
    try:
        subjectfile = open(os.path.join(conf.subjects_base, subject,
            "subject.xml"))
    except:
        raise Exception("Subject %s not found." % repr(subject))

    assessable_worksheets = []
    # Read in data about the subject
    subjectdom = minidom.parse(subjectfile)
    subjectfile.close()
    # TEMP: All of this is for a temporary XML format, which will later
    # change.
    worksheetsdom = subjectdom.documentElement
    worksheets = []     # List of string IDs
    for worksheetdom in worksheetsdom.childNodes:
        if worksheetdom.nodeType == worksheetdom.ELEMENT_NODE:
            # (Note: assessable will default to False, unless it is explicitly
            # set to "true").
            if worksheetdom.getAttribute("assessable") == "true":
                assessable_worksheets.append(worksheetdom.getAttribute("id"))

    return assessable_worksheets

def get_marks_header(worksheets):
    """
    Given a list of strings - the assessable worksheets - returns a new list
    of strings - the column headings for the marks section of the CSV output.
    """
    return worksheets + ["Total %", "Mark"]

def get_marks_user(subject, worksheets, user):
    """
    Given a subject, a list of strings (the assessable worksheets), and a user
    object, returns the user's percentage for each worksheet, overall, and
    their final mark, as a list of strings, in a manner which corresponds to
    the headings produced by get_marks_header.
    """
    # NOTE: This code is copy/edited from
    # www/apps/tutorial/__init__.py:handle_subject_menu
    # Should be factored out of there.

    worksheet_pcts = []
    # As we go, calculate the total score for this subject
    # (Assessable worksheets only, mandatory problems only)
    problems_done = 0
    problems_total = 0

    for worksheet in worksheets:
        try:
            # We simply ignore optional exercises here
            mand_done, mand_total, _, _ = (
                db.calculate_score_worksheet(user.login, subject,
                    worksheet))
            worksheet_pcts.append(float(mand_done) / mand_total)
            problems_done += mand_done
            problems_total += mand_total
        except common.db.DBException:
            # Worksheet is probably not in database yet
            pass
    problems_pct = float(problems_done) / problems_total
    problems_pct_int = (100 * problems_done) / problems_total
    # XXX Marks calculation (should be abstracted out of here!)
    # percent / 16, rounded down, with a maximum mark of 5
    max_mark = 5
    mark = min(problems_pct_int / 16, max_mark)
    return worksheet_pcts + [problems_pct, mark]

def writeuser(subject, worksheets, user, csvfile):
    userdata = get_userdata(user)
    marksdata = get_marks_user(subject, worksheets, user)
    csvfile.writerow(userdata + marksdata)

try:
    # Get the list of assessable worksheets from the subject.xml file,
    # and the list of all users from the DB.
    worksheets = get_assessable_worksheets(subject)
    db = common.db.DB()
    list = db.get_users()
except Exception, message:
    print >>sys.stderr, "Error: " + str(message)
    sys.exit(1)

# Start writing the CSV file - header
csvfile = csv.writer(sys.stdout)
csvfile.writerow(userdata_header + get_marks_header(worksheets))

list.sort(key=lambda user: user.login)
for user in list:
    writeuser(subject, worksheets, user, csvfile)

