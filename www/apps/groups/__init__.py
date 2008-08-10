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

from common import (util, caps)
import common.db

def handle(req):
    # Set request attributes
    req.content_type = "text/html"
    req.styles = ["media/groups/groups.css"]
    req.scripts = [
        "media/groups/groups.js",
        "media/common/util.js",
        "media/common/json2.js",
    ]
    req.write_html_head_foot = True     # Have dispatch print head and foot

    req.write('<div id="ivle_padding">\n')
    # Show a group panel per enrolment
    db = common.db.DB()
    try:
        subjects = db.get_enrolment(req.user.login)
        # Sort by year,semester,subj_code (newer subjects first)
        # Leave all fields as strings, just in case (eg. semester='y')
        subjects.sort(key=lambda(subject):
                          (subject["year"],subject["semester"],subject["subj_code"]),
                      reverse=True)
        if len(subjects) == 0:
            req.write("<p>Error: You are not currently enrolled in any subjects."
                      "</p>\n")
        for subject in subjects:
            show_subject_panel(req, db, subject['offeringid'],
                subject['subj_name'])
        if req.user.hasCap(caps.CAP_MANAGEGROUPS):
            show_groupadmin_panel(req, db)
        
        req.write("</div>\n")
    finally:
        db.close()

def show_groupadmin_panel(req, db):
    """
    Shows the group admin panel
    """
    req.write("<hr/>\n")
    req.write("<h1>Group Administration</h1>")
    # Choose subject
    subjects = db.get_subjects()
    req.write("<p>Manage a subject's groups:</p>\n")
    req.write("<select id=\"subject_select\">\n")
    for s in subjects:
        req.write("    <option value=\"%d\">%s: %s</option>\n"%
            (s['subjectid'], s['subj_code'], s['subj_name']))
    req.write("</select>\n")
    req.write("<input type=\"button\" value=\"Manage Subject\" \
        onclick=\"manage_subject()\" />\n")
    req.write("<div id=\"subject_div\"></div>")

def show_subject_panel(req, db, offeringid, subj_name):
    """
    Show the group management panel for a particular subject.
    Prints to req.
    """
    # Get the groups this user is in, for this offering
    groups = db.get_groups_by_user(req.user.login, offeringid=offeringid)
    if len(groups) == 0:
        return

    req.write("<div id=\"subject%d\"class=\"subject\">"%offeringid)
    req.write("<h1>%s</h1>\n" % cgi.escape(subj_name))
    for groupid, groupnm, group_nick, is_member in groups:
        if group_nick is None:
            group_nick = "";
        req.write("<h2>%s (%s)</h2>\n" %
            (cgi.escape(group_nick), cgi.escape(groupnm)))
        if is_member:
            req.write('<p>You are a member of this group.</p>\n')
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
        req.write("<ul>\n")
        for user in db.get_projectgroup_members(groupid):
            req.write("<li>%s (%s)</li>" %
                      (cgi.escape(user['fullname']),
                       cgi.escape(user['login'])))
        req.write("</ul>\n")

    req.write("</div>")
