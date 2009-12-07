

import ivle.database
from ivle.database import ProjectSet, Subject, Semester, Offering

from ivle.webapp.base.rest import (XHTMLRESTView, named_operation,
                                   require_permission)

from ivle.webapp.errors import NotFound

class OfferingRESTView(XHTMLRESTView):
    """REST view for a subject.
      
    This view allows for added a ProjectSet to an existing subject."""

    template = "subject.html"

    def new_project_url(self, projectset):
        return "/api/subjects/%s/%s/%s/+projectsets/%d/+projects/+new" % (
            self.context.subject.short_name, self.context.semester.year,
            self.context.semester.semester, projectset.id)

    @named_operation('edit')
    def add_projectset(self, req, group_size):
        """Add a new ProjectSet"""
        new_projectset = ProjectSet()
        if group_size == '':
            new_projectset.max_students_per_group = None
        else:
            new_projectset.max_students_per_group = int(group_size)
        new_projectset.offering = self.context

        req.store.add(new_projectset)
        req.store.flush()

        self.ctx['projectset'] = new_projectset
        self.ctx['projects'] = []
        self.ctx['new_project_url'] = self.new_project_url(new_projectset)

        self.template = 'templates/projectset_fragment.html'

        return {'success': True, 'projectset_id': new_projectset.id}
