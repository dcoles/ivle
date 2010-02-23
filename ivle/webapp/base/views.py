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

# Author: Matt Giuca, Will Grant

class BaseView(object):
    """
    Abstract base class for all view objects.
    """

    subpath_allowed = False
    offsite_posts_allowed = False

    def __init__(self, req, context, subpath=None):
        self.req = req
        self.context = context
        if self.subpath_allowed:
            self.subpath = subpath

    def render(self, req):
        raise NotImplementedError()

    def get_permissions(self, user, config):
        return self.context.get_permissions(user, config)

    def authorize(self, req):
        self.perms = self.get_permissions(req.user, req.config)

        return self.permission is None or self.permission in self.perms
