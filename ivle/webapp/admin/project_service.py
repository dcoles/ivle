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

import ivle.database
from ivle.data import ProjectSet, Project, Subject, Semester, Offering

from ivle.webapp.base.rest import (XHTMLRESTView, named_operation,
                                   require_permission)
from ivle.webapp.errors import NotFound

class ProjectSETRESTView(XHTMLRESTView):
    """Rest view for a project.
    
    Add new, delete, edit functionality is given here."""
    template = "projectset.html"
    
    def __init__(self, req, subject, year, semester, projectset):
        self.context = req.store.find(Offering,
            Offering.subject_id == Subject.id,
            Subject.short_name == unicode(subject),
            Offering.semester_id == Semester.id,
            Semester.year == unicode(year),
            Semester.semester == unicode(semester))
        
        if self.context is None:
            raise NotFound()
        
        self.projectset = req.store.find(ProjectSet,
            ProjectSet.offering_id == self.context.id,
            ProjectSet.id == int(projectset))
    
    @require_permission('edit')
    def PUT(self, req, max_students):
        """Add a new ProjectSet"""
        new_projectset = ProjectSet()
        new_projectset.max_students = int(max_students)
        new_projectset.offering = self.context
        
        
