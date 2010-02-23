# IVLE - Informatics Virtual Learning Environment
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

# Author: Nick Chadwick

import datetime

import formencode
import formencode.validators

import ivle.database
from ivle.database import ProjectSet, Project, Subject, Semester, Offering

from ivle.webapp.base.forms import VALID_URL_NAME
from ivle.webapp.base.rest import (XHTMLRESTView, named_operation,
                                   require_permission)
from ivle.webapp.errors import NotFound, BadRequest

class ProjectSetRESTView(XHTMLRESTView):
    """Rest view for a projectset.
    
    Add new, delete, edit functionality is given here."""
    template = "templates/projectset_fragment.html"

    def _project_url(self, project):
        return "/subjects/%s/%s/%s/+projects/%s" % \
                (self.context.offering.subject.short_name,
                 self.context.offering.semester.year,
                 self.context.offering.semester.semester,
                 project.short_name)

    @named_operation('edit')
    def add_project(self, req, name, short_name, deadline, synopsis, url):
        """Add a Project to this ProjectSet"""
        if not VALID_URL_NAME.match(short_name):
            raise BadRequest(
                "Project names must consist of a lowercase alphanumeric "
                "character followed by any number of lowercase alphanumerics, "
                "., +, - or _.")

        if req.store.find(
            Project,
            Project.short_name == unicode(short_name),
            Project.project_set_id == ProjectSet.id,
            ProjectSet.offering == self.context.offering).one():
            raise BadRequest(
                "A project with that URL name already exists in this offering."
                )

        try:
            formencode.validators.URL().to_python(url)
        except formencode.Invalid, e:
            raise BadRequest(str(e))

        new_project = Project()
        new_project.name = unicode(name)
        new_project.short_name = unicode(short_name)
        new_project.url = unicode(url)
        new_project.synopsis = unicode(synopsis)
        try:
            new_project.deadline = datetime.datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise BadRequest("deadline must be in YYYY-MM-DD HH:MM:ss")
        new_project.project_set = self.context

        req.store.add(new_project)
        req.store.flush()
    
        self.template = "templates/project_fragment.html"
        self.ctx['req'] = req
        self.ctx['project'] = new_project

        return {'success': True, 'projectset_id': self.context.id}
