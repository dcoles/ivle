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

import cgi
import urlparse
import inspect

import cjson

from ivle.webapp.base.views import BaseView
from ivle.webapp.errors import BadRequest, MethodNotAllowed, Unauthorized

class RESTView(BaseView):
    """
    A view which provides a RESTful interface. The content type is
    unspecified (see JSONRESTView for a specific content type).
    """
    content_type = "application/octet-stream"

    def __init__(self, req, *args, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def render(self, req):
        raise NotImplementedError()

class JSONRESTView(RESTView):
    """
    A special case of RESTView which deals entirely in JSON.
    """
    content_type = "application/json"

    _allowed_methods = property(
        lambda self: [m for m in ('GET', 'PUT', 'PATCH')
                      if hasattr(self, m)] + ['POST'])

    def authorize(self, req):
        return True # Real authz performed in render().

    def authorize_method(self, req, op):
        if not hasattr(op, '_rest_api_permission'):
            raise Unauthorized()

        if op._rest_api_permission not in self.get_permissions(req.user):
            raise Unauthorized()
    
    def convert_bool(self, value):
        if value in ('True', 'true', True):
            return True
        elif value in ('False', 'false', False):
            return False
        else:
            raise BadRequest()

    def render(self, req):
        if req.method not in self._allowed_methods:
            raise MethodNotAllowed(allowed=self._allowed_methods)

        if req.method == 'GET':
            self.authorize_method(req, self.GET)
            outjson = self.GET(req)
        # Since PATCH isn't yet an official HTTP method, we allow users to
        # turn a PUT into a PATCH by supplying a special header.
        elif req.method == 'PATCH' or (req.method == 'PUT' and
              'X-IVLE-Patch-Semantics' in req.headers_in and
              req.headers_in['X-IVLE-Patch-Semantics'].lower() == 'yes'):
            self.authorize_method(req, self.PATCH)
            try:
                input = cjson.decode(req.read())
            except cjson.DecodeError:
                raise BadRequest('Invalid JSON data')
            outjson = self.PATCH(req, input)
        elif req.method == 'PUT':
            self.authorize_method(req, self.PUT)
            try:
                input = cjson.decode(req.read())
            except cjson.DecodeError:
                raise BadRequest('Invalid JSON data')
            outjson = self.PUT(req, input)
        # POST implies named operation.
        elif req.method == 'POST':
            # TODO: Check Content-Type and implement multipart/form-data.
            data = req.read()
            opargs = dict(cgi.parse_qsl(data, keep_blank_values=1))
            try:
                opname = opargs['ivle.op']
                del opargs['ivle.op']
            except KeyError:
                raise BadRequest('No named operation specified.')

            try:
                op = getattr(self, opname)
            except AttributeError:
                raise BadRequest('Invalid named operation.')

            if not hasattr(op, '_rest_api_callable') or \
               not op._rest_api_callable:
                raise BadRequest('Invalid named operation.')

            self.authorize_method(req, op)

            # Find any missing arguments, except for the first two (self, req)
            (args, vaargs, varkw, defaults) = inspect.getargspec(op)
            args = args[2:]

            # To find missing arguments, we eliminate the provided arguments
            # from the set of remaining function signature arguments. If the
            # remaining signature arguments are in the args[-len(defaults):],
            # we are OK.
            unspec = set(args) - set(opargs.keys())
            if unspec and not defaults:
                raise BadRequest('Missing arguments: ' + ', '.join(unspec))

            unspec = [k for k in unspec if k not in args[-len(defaults):]]

            if unspec:
                raise BadRequest('Missing arguments: ' + ', '.join(unspec))

            # We have extra arguments if the are no match args in the function
            # signature, AND there is no **.
            extra = set(opargs.keys()) - set(args)
            if extra and not varkw:
                raise BadRequest('Extra arguments: ' + ', '.join(extra))

            outjson = op(req, **opargs)

        req.content_type = self.content_type
        if outjson is not None:
            req.write(cjson.encode(outjson))
            req.write("\n")

class named_operation(object):
    '''Declare a function to be accessible to HTTP users via the REST API.
    '''
    def __init__(self, permission):
        self.permission = permission

    def __call__(self, func):
        func._rest_api_callable = True
        func._rest_api_permission = self.permission
        return func

class require_permission(object):
    '''Declare the permission required for use of a method via the REST API.
    '''
    def __init__(self, permission):
        self.permission = permission

    def __call__(self, func):
        func._rest_api_permission = self.permission
        return func
