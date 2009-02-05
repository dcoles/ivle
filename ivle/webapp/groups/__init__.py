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

# TODO Does not distinguish between current and past subjects.

from ivle import caps
from ivle.database import Subject

from ivle.webapp.base.plugins import BasePlugin
from ivle.webapp.base.xhtml import XHTMLView

class GroupsView(XHTMLView):
    """
    The groups view
    """
    template = 'template.html'
    appname = 'groups' # XXX

    def populate(self, req, ctx):
        # Set request attributes
        req.styles = ["media/groups/groups.css"]
        req.scripts = [
            "media/groups/groups.js",
            "media/common/util.js",
            "media/common/json2.js",
        ]

        # Show a group panel per enrolment
        ctx['get_user_groups'] = req.user.get_groups
        ctx['enrolments'] = req.user.active_enrolments
        ctx['manage_subjects'] = req.store.find(Subject) if \
              req.user.hasCap(caps.CAP_MANAGEGROUPS) else []


class Plugin(BasePlugin):
    """
    The Plugin class for the group admin plugin.
    """
    urls = [
        ('groups/', GroupsView),
    ]
