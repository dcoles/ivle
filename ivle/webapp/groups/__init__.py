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

from ivle.database import ProjectSet

from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.errors import NotFound

class GroupsView(XHTMLView):
    """
    The groups view
    """
    template = 'template.html'
    tab = 'subjects'
    permission = 'admin_groups'

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['groups.css']
        self.plugin_scripts[Plugin] = ['groups.js']

        ctx['req'] = req
        ctx['projectset'] = self.context

class Plugin(ViewPlugin, MediaPlugin):
    """
    The Plugin class for the group admin plugin.
    """
    views = [(ProjectSet, '+index', GroupsView)]

    media = 'media'
