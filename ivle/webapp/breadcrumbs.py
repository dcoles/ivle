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

class Breadcrumber(object):
    def __init__(self, req):
        self.req = req
        self.index = {}

        for plugin in req.config.plugins.values():
            if hasattr(plugin, 'breadcrumbs'):
                for cls in plugin.breadcrumbs:
                    assert cls not in self.index
                    self.index[cls] = plugin.breadcrumbs[cls]

    def crumb(self, obj):
        if type(obj) not in self.index:
            return None
        return self.index[type(obj)](self.req, obj)