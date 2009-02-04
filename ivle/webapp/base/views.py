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

import inspect
import cgi
import os.path

import cjson
import genshi.template

import ivle.conf
import ivle.util
from ivle.webapp.errors import BadRequest, MethodNotAllowed

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

    _allowed_methods = property(
        lambda self: [m for m in ('GET', 'PUT', 'PATCH')
                      if hasattr(self, m)] + ['POST'])

    def render(self, req):
        if req.method not in self._allowed_methods:
            raise MethodNotAllowed(allowed=self._allowed_methods)

        if req.method == 'GET':
            outjson = self.GET(req)
        # Since PATCH isn't yet an official HTTP method, we allow users to
        # turn a PUT into a PATCH by supplying a special header.
        elif req.method == 'PATCH' or (req.method == 'PUT' and
              'X-IVLE-Patch-Semantics' in req.headers_in and
              req.headers_in['X-IVLE-Patch-Semantics'].lower() == 'yes'):
            outjson = self.PATCH(req, cjson.decode(req.read()))
        elif req.method == 'PUT':
            outjson = self.PUT(req, cjson.decode(req.read()))
        # POST implies named operation.
        elif req.method == 'POST':
            # TODO: Check Content-Type and implement multipart/form-data.
            opargs = dict(cgi.parse_qsl(req.read()))
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

            # Find any missing arguments, except for the first one (self).
            (args, vaargs, varkw, defaults) = inspect.getargspec(op)
            args = args[1:]

            # To find missing arguments, we eliminate the provided arguments
            # from the set of remaining function signature arguments. If the
            # remaining signature arguments are in the args[-len(defaults):],
            # we are OK.
            unspec = set(args) - set(opargs.keys())
            if unspec and not defaults:
                raise BadRequest('Missing arguments: ' + ','.join(unspec))

            unspec = [k for k in unspec if k not in args[-len(defaults):]]

            if unspec:
                raise BadRequest('Missing arguments: ' + ','.join(unspec))

            # We have extra arguments if the are no match args in the function
            # signature, AND there is no **.
            extra = set(opargs.keys()) - set(args)
            if extra and not varkw:
                raise BadRequest('Extra arguments: ' + ', '.join(extra))

            outjson = op(**opargs)
        else:
            raise AssertionError('Unknown method somehow got through.')

        req.content_type = self.content_type
        if outjson is not None:
            req.write(cjson.encode(outjson))
            req.write("\n")

def named_operation(meth):
    '''Declare a function to be accessible to HTTP users via the REST API.
    '''
    meth._rest_api_callable = True
    return meth

class XHTMLView(BaseView):
    """
    A view which provides a base class for views which need to return XHTML
    It is expected that apps which use this view will be written using Genshi
    templates.
    """
    def __init__(self, req, **kwargs):
        for key in kwargs:
          setattr(self, key, kwargs[key])
        
    def render(self, req):
        req.content_type = 'text/html' # TODO: Detect application/xhtml+xml
        ctx = genshi.template.Context()
        self.populate(req, ctx)
        self.populate_headings(req, ctx)
        
        ctx['app_styles'] = req.styles
        ctx['scripts'] = req.scripts
        ctx['scripts_init'] = req.scripts_init
        app_template = os.path.join(os.path.dirname(
                        inspect.getmodule(self).__file__), self.app_template) 
        req.write_html_head_foot = False
        loader = genshi.template.TemplateLoader(".", auto_reload=True)
        tmpl = loader.load(app_template)
        app = tmpl.generate(ctx)
        ctx['app_template'] = app
        tmpl = loader.load(os.path.join(os.path.dirname(__file__), 
                                                        'ivle-headings.html'))
        req.write(tmpl.generate(ctx).render('xhtml', doctype='xhtml'))

    def populate_headings(self, req, ctx):
        ctx['favicon'] = None
        ctx['root_dir'] = ivle.conf.root_dir
        ctx['public_host'] = ivle.conf.public_host
        ctx['write_javascript_settings'] = req.write_javascript_settings
        if req.user:
            ctx['login'] = req.user.login
            ctx['logged_in'] = True
            ctx['nick'] = req.user.nick
        else:
            ctx['login'] = None
        ctx['publicmode'] = req.publicmode
        ctx['apps_in_tabs'] = []
        for urlname in ivle.conf.apps.apps_in_tabs:
            new_app = {}
            app = ivle.conf.apps.app_url[urlname]
            new_app['this_app'] = urlname == self.appname
            if app.icon:
                new_app['has_icon'] = True
                icon_dir = ivle.conf.apps.app_icon_dir
                icon_url = ivle.util.make_path(os.path.join(icon_dir, app.icon))
                new_app['icon_url'] = icon_url
                if new_app['this_app']:
                    ctx['favicon'] = icon_url
            else:
                new_app['has_icon'] = False
            new_app['path'] = ivle.util.make_path(urlname)
            new_app['desc'] = app.desc
            new_app['name'] = app.name
            ctx['apps_in_tabs'].append(new_app)
