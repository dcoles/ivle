# IVLE
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

# App: groups
# Author: Matt Giuca
# Date: 21/7/2008

# Allows students and tutors to manage project groups.

# XXX Does not distinguish between current and past subjects.

import cgi

from common import util
import common.db

def handle(req):
    # Set request attributes
    req.content_type = "text/html"
    req.styles = ["media/groups/groups.css"]
    req.scripts = ["media/groups/groups.js"]
    req.write_html_head_foot = True     # Have dispatch print head and foot

    req.write('<div id="ivle_padding">\n')
    # Show a group panel per enrolment
    db = common.db.DB()
    try:
        subjects = db.get_enrolment(req.user.login)
        # Sort by year,semester,subj_code (newer subjects first)
        # Leave all fields as strings, just in case (eg. semester='y')
        subjects.sort(key=lambda (_oid,subj_code,_sn,_ssn,year,semester):
                            (year,semester,subj_code),
                      reverse=True)
        if len(subjects) == 0:
            req.write("<p>Error: You are not currently enrolled in any subjects."
                      "</p>\n")
        for offeringid,_,subj_name,_,_,_ in subjects:
            show_subject_panel(req, db, offeringid, subj_name)
        req.write("</div>\n")
    finally:
        db.close()

def show_subject_panel(req, db, offeringid, subj_name):
    """
    Show the group management panel for a particular subject.
    Prints to req.
    """
    req.write("<h1>%s</h1>\n" % cgi.escape(subj_name))
    # Get the groups this user is in, for this offering
    groups = db.get_groups_by_user(req.user.login, offeringid=offeringid)
    for groupid, groupnm, group_nick, is_member in groups:
        req.write("<h2>%s (%s)</h2>\n" %
            (cgi.escape(group_nick), cgi.escape(groupnm)))
        if is_member:
            req.write('<p>You are in this group.\n'
                '  <input type="button" onclick="manage(&quot;%s&quot;)" '
                'value="Manage" /></p>\n' % (cgi.escape(groupnm)))
        else:
            req.write('<p>You have been invited to this group.</p>\n')
            req.write('<p>'
                '<input type="button" '
                'onclick="accept(&quot;%(groupnm)s&quot;)" '
                'value="Accept" />\n'
                '<input type="button" '
                'onclick="decline(&quot;%(groupnm)s&quot;)" '
                'value="Decline" />\n'
                '</p>\n' % {"groupnm": cgi.escape(groupnm)})
        req.write("<h3>Members</h3>\n")
        req.write("<table>\n")
        # TODO: Fill in members table
        req.write("</table>\n")

    if True:        # XXX Only if offering allows students to create groups
        req.write('<input type="button" onclick="create(%d)" '
            'value="Create Group" />\n' % offeringid)
