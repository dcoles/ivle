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

# Author: Matt Giuca, Will Grant

'''
Allows students and tutors to manage project groups.
'''

from ivle.database import Subject, Offering, Semester

from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.base.xhtml import XHTMLView

class GroupsView(XHTMLView):
    """
    The groups view
    """
    template = 'template.html'
    tab = 'groups'

    def __init__(self, req, subject, year, semester):
        """Find the given offering by subject, year and semester."""
        self.context = req.store.find(Offering,
            Offering.subject_id == Subject.id,
            Subject.code == subject,
            Offering.semester_id == Semester.id,
            Semester.year == year,
            Semester.semester == semester).one()
        
        if not self.context:
            raise NotFound()

    def authorize(self, req):
        enrolment = self.context.get_enrolment(req.user)
        if not enrolment:
            return False
        return req.user.admin or enrolment.role in (u'tutor', u'lecturer')

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['groups.css']
        self.plugin_scripts[Plugin] = ['groups.js']

        ctx['offering'] = self.context

class Plugin(ViewPlugin, MediaPlugin):
    """
    The Plugin class for the group admin plugin.
    """
    urls = [
        ('/subjects/:subject/:year/:semester/+groups/', GroupsView),
    ]

    media = 'media'
    help = {'Groups': 'help.html'}
