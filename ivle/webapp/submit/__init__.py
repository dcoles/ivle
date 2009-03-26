# IVLE
# Copyright (C) 2007-2009 The University of Melbourne
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

# Author: Will Grant

"""Project submissions user interface."""

from ivle.database import (User, ProjectGroup, Offering, Subject, Semester,
                           ProjectSet)
from ivle.webapp.errors import NotFound
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin


class SubmitView(XHTMLView):
    """A view to submit a Subversion repository path for a project."""
    template = 'submit.html'
    tab = 'files'
    permission = 'submit_project'

    def __init__(self, req, rtype, rname, path):
        # We need to work out which entity owns the repository, so we look
        # at the first two path segments. The first tells us the type.
        if rtype == 'users':
            self.context = User.get_by_login(req.store, rname)
        elif rtype == 'groups':
            namebits = rname.split('_', 3)
            if len(namebits) != 4:
                raise NotFound()
            self.context = req.store.find(ProjectGroup,
                ProjectGroup.name == namebits[3],
                ProjectGroup.project_set_id == ProjectSet.id,
                ProjectSet.offering_id == Offering.id,
                Offering.subject_id == Subject.id,
                Subject.short_name == namebits[0],
                Offering.semester_id == Semester.id,
                Semester.year == namebits[1],
                Semester.semester == namebits[2]).one()
        else:
            raise NotFound()

        if self.context is None:
            raise NotFound()

    def populate(self, req, ctx):
        pass

class Plugin(ViewPlugin):
    urls = [
        ('+submit/:rtype/:rname/*path', SubmitView),
    ]
