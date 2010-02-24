

import ivle.database
from ivle.database import ProjectSet, Subject, Semester, Offering

from ivle.webapp.admin.projectservice import ProjectSetRESTView
from ivle.webapp.groups import GroupsView
from ivle.webapp.base.rest import (XHTMLRESTView, named_operation,
                                   require_permission)
from ivle.webapp.errors import NotFound

class OfferingRESTView(XHTMLRESTView):
    """REST view for a subject.
      
    This view allows for added a ProjectSet to an existing subject."""

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

        self.ctx['req'] = req
        self.ctx['projectset'] = new_projectset
        self.ctx['projects'] = []
        self.ctx['GroupsView'] = GroupsView
        self.ctx['ProjectSetRESTView'] = ProjectSetRESTView

        self.template = 'templates/projectset_fragment.html'

        return {'success': True, 'projectset_id': new_projectset.id}
