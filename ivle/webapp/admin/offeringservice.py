

import ivle.database
from ivle.database import ProjectSet, Subject, Semester, Offering

from ivle.webapp.base.rest import (XHTMLRESTView, named_operation,
                                   require_permission)

from ivle.webapp.errors import NotFound

class OfferingRESTView(XHTMLRESTView):
    """REST view for a subject.
      
    This view allows for added a ProjectSet to an existing subject."""

    template = "subject.html"

    def __init__(self, req, subject, year, semester):

        self.context = req.store.find(Offering,
                Offering.subject_id == Subject.id,
                Subject.short_name == unicode(subject),
                Offering.semester_id == Semester.id,
                Semester.year == unicode(year),
                Semester.semester == unicode(semester)).one()

        if self.context is None:
            raise NotFound()

    def new_project_url(self, projectset):
        return "/api/subjects/" + str(self.context.subject.id) + "/" +\
               self.context.semester.year + "/" +\
               self.context.semester.semester + "/+projectsets/" +\
               (str(projectset.id)) + "/+projects/+new"

    @named_operation('edit')
    def add_projectset(self, req, group_size):
        """Add a new ProjectSet"""
        new_projectset = ProjectSet()
        new_projectset.max_students_per_group = int(group_size)
        new_projectset.offering = self.context

        req.store.add(new_projectset)
        req.store.flush()

        self.ctx['group_size'] = new_projectset.max_students_per_group
        self.ctx['projectset_id'] = new_projectset.id
        self.ctx['projects'] = []
        self.ctx['new_project_url'] = self.new_project_url(new_projectset)

        self.template = 'templates/projectset_fragment.html'

        return {'success': True, 'projectset_id': new_projectset.id}
