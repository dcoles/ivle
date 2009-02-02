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

from ivle import caps
from ivle.database import Subject
from ivle import util

import genshi
import genshi.core
import genshi.template

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

    ctx = genshi.template.Context()
    
    ctx['enrolments'] = []
    # Show a group panel per enrolment
    enrolments = req.user.active_enrolments
    if enrolments.count() == 0:
        ctx['no_enrolments'] = True
    else:
        ctx['no_enrolments'] = False
    
    for enrolment in enrolments:
        add_subject_panel(req, enrolment.offering, ctx)
        
    if req.user.hasCap(caps.CAP_MANAGEGROUPS):
        ctx['manage_groups'] = True
        ctx['manage_subjects'] = []
        subjects = req.store.find(Subject)
        for s in subjects:
            new_s = {}
            new_s['id'] = s.id
            new_s['name'] = s.name
            new_s['code'] = s.code
            ctx['manage_subjects'].append(new_s)
    else:
        ctx['manage_groups'] = False
  
    loader = genshi.template.TemplateLoader(".", auto_reload=True)
    tmpl = loader.load(util.make_local_path("apps/groups/template.html"))
    
    req.write(tmpl.generate(ctx).render('html'))

def add_subject_panel(req, offering, ctx):
    """
    Show the group management panel for a particular subject.
    Prints to req.
    """
    # Get the groups this user is in, for this offering
    groups = req.user.get_groups(offering)
    if groups.count() == 0:
        return
    
    offering_groups = {}
    
    offering_groups['offering_id'] = offering.id
    offering_groups['offering_name'] = offering.subject.name
    offering_groups['groups'] = []
    
    #TODO: Use a better way to manage group membership and invitations
    for group in groups:
        new_group = {}
        new_group['nick'] = cgi.escape(group.nick if group.nick else '')
        new_group['name'] = cgi.escape(group.name)
        
        # XXX - This should be set to reflect whether or not a user is invited
        #     - or if they have accepted the offer
        new_group['is_member'] = True
        new_group['members'] = []
        
        for user in group.members:
            member = {}
            member['fullname'] = cgi.escape(user.fullname)
            member['login'] = cgi.escape(user.login)
            new_group['members'].append(member)
        offering_groups['groups'].append(new_group)

    ctx['enrolments'].append(offering_groups)
