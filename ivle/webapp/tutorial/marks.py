# IVLE
# Copyright (C) 2007-2010 The University of Melbourne
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

# Author: Matt Giuca

"""Worksheet marks reporting functionality.

Displays students' worksheet marks to users with sufficient privileges.
"""

import datetime
import csv
import urllib

import ivle.database
import ivle.worksheet.utils
from ivle.webapp.base.views import BaseView
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.media import media_url

class WorksheetsMarksView(XHTMLView):
    """View for presenting all students' individual marks for worksheets."""
    permission = 'view_worksheet_marks'
    template = 'templates/worksheets_marks.html'
    tab = 'subjects'

    def populate(self, req, ctx):
        error = None
        offering = self.context
        ctx['req'] = req
        ctx['context'] = offering
        ctx['urllib'] = urllib
        ctx['WorksheetsMarksCSVView'] = WorksheetsMarksCSVView

        # User may supply a "cutoff date" to calculate marks as of that date
        # Default to current time
        cutoff = datetime.datetime.now()
        data = dict(req.get_fieldstorage())
        if data.get('cutoff') is not None:
            try:
                cutoff = datetime.datetime.strptime(data.get('cutoff'),
                                                    "%Y-%m-%d %H:%M:%S")
            except ValueError:
                error = (
                    "Invalid date format: '%s' (must be YYYY-MM-DD H:M:S)."
                        % data.get('cutoff'))
        ctx['cutoff'] = cutoff
        ctx['error'] = error

        # "worksheets" is a list of (assessable) worksheet names
        worksheets = offering.worksheets.find(assessable=True)
        ctx['worksheets'] = [ws.name for ws in worksheets]

        # "students" is a list of tuples:
        # (user, worksheet_pcts, total_pct, mark)
        # user is a User object, worksheet_pcts is a list of floats (one per
        # worksheet), total_pct is a float, mark is an int
        ctx['students'] = students = []
        # Get all users enrolled in this offering
        users = req.store.find(ivle.database.User,
                       ivle.database.User.id == ivle.database.Enrolment.user_id,
                       offering.id == ivle.database.Enrolment.offering).order_by(
                            ivle.database.User.login)
        for user in users:
            worksheet_pcts, total_pct, mark = get_marks_user(req, worksheets,
                                                user, as_of=cutoff)
            students.append((user, worksheet_pcts, total_pct, mark))

class WorksheetsMarksCSVView(BaseView):
    """View for presenting all students' individual marks for worksheets."""
    permission = 'view_worksheet_marks'
    template = 'templates/worksheets_marks.html'
    tab = 'subjects'

    def render(self, req):
        offering = self.context

        # User may supply a "cutoff date" to calculate marks as of that date
        # Default to current time
        cutoff = datetime.datetime.now()
        data = dict(req.get_fieldstorage())
        if data.get('cutoff') is not None:
            try:
                cutoff = datetime.datetime.strptime(data.get('cutoff'),
                                                    "%Y-%m-%d %H:%M:%S")
            except ValueError:
                req.write(
                    "Invalid date format: '%s' (must be YYYY-MM-DD H:M:S)."
                        % data.get('cutoff'))
                return

        req.content_type = "text/csv"
        req.headers_out.add('Content-Disposition',
            "attachment; filename=marks-%s-%ss%s.csv" %
            (offering.subject.short_name, offering.semester.year,
             offering.semester.semester))

        # "worksheets" is a list of (assessable) worksheet names
        worksheets = offering.worksheets.find(assessable=True)

        # Start writing the CSV file - header
        csvfile = csv.writer(req)
        csvfile.writerow(csv_get_header(worksheets))

        # Get all users enrolled in this offering
        users = req.store.find(ivle.database.User,
                   ivle.database.User.id == ivle.database.Enrolment.user_id,
                   offering.id == ivle.database.Enrolment.offering).order_by(
                        ivle.database.User.login)
        for user in users:
            csv_writeuser(req, worksheets, user, csvfile, cutoff)

def get_marks_user(req, worksheets, user, as_of=None):
    """Gets marks for a particular user for a particular set of worksheets.
    @param worksheets: List of Worksheet objects to get marks for.
    @param user: User to get marks for.
    @param as_of: Optional datetime. If supplied, gets the marks as of as_of.
    @returns: (worksheet_pcts, total_pct, mark)
    """
    worksheet_pcts = []
    # As we go, calculate the total score for this subject
    # (Assessable worksheets only, mandatory problems only)
    problems_done = 0
    problems_total = 0

    for worksheet in worksheets:
        # We simply ignore optional exercises here
        mand_done, mand_total, _, _ = (
            ivle.worksheet.utils.calculate_score(req.store, user, worksheet,
                                                 as_of))
        if mand_total > 0:
            worksheet_pcts.append(float(mand_done) / mand_total)
        else:
            # Avoid Div0, just give everyone 0 marks if there are none
            worksheet_pcts.append(0.0)
        problems_done += mand_done
        problems_total += mand_total
    percent, mark, _ = (
        ivle.worksheet.utils.calculate_mark(problems_done, problems_total))
    return (worksheet_pcts, float(percent)/100, mark)

def csv_get_userdata(user):
    """
    Given a User object, returns a list of strings for the user data which
    will be part of the output for this user.
    (This is not marks, it's other user data).
    """
    last_login = ("N/A" if user.last_login is None else
                    user.last_login.strftime("%Y-%m-%d"))
    return [user.studentid or "N/A", user.login, user.fullname, last_login]

csv_userdata_header = ["Student ID", "Login", "Full name", "Last login"]
def csv_get_header(worksheets):
    """
    Given a list of Worksheet objects (the assessable worksheets), returns a
    list of strings -- the column headings for the marks section of the CSV
    output.
    """
    return (csv_userdata_header + [ws.name for ws in worksheets]
            + ["Total %", "Mark"])

def csv_writeuser(req, worksheets, user, csvfile, cutoff=None):
    userdata = csv_get_userdata(user)
    worksheet_pcts, total_pct, mark = get_marks_user(req, worksheets, user,
                                                     cutoff)
    data = userdata + worksheet_pcts + [total_pct, mark]
    # CSV writer can't handle non-ASCII characters. Encode to UTF-8.
    data = [unicode(x).encode('utf-8') for x in data]
    csvfile.writerow(data)
