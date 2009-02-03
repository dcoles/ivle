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

import cjson

class BaseView(object):
    """
    Abstract base class for all view objects.
    """
    def __init__(self, req, **kwargs):
        pass
    def render(self, req):
        pass

class RESTView(BaseView):
    """
    A view which provides a RESTful interface. The content type is
    unspecified (see JSONRESTView for a specific content type).
    """
    content_type = "application/octet-stream"

    def __init__(self, req, *args, **kwargs):
        pass

    def render(self, req):
        if req.method == 'GET':
            outstr = self.GET(req)
        # XXX PATCH hack
        if req.method == 'PUT':
            outstr = self.PATCH(req, req.read())
        req.content_type = self.content_type
        req.write(outstr)

class JSONRESTView(RESTView):
    """
    A special case of RESTView which deals entirely in JSON.
    """
    content_type = "application/json"

    def render(self, req):
        if req.method == 'GET':
            outjson = self.GET(req)
        # XXX PATCH hack
        if req.method == 'PUT':
            outjson = self.PATCH(req, cjson.decode(req.read()))
        req.content_type = self.content_type
        if outjson is not None:
            req.write(cjson.encode(outjson))
            req.write("\n")
