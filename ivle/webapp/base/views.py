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
import os.path

import cjson
import genshi.template

import ivle.conf
import ivle.util

from ivle.webapp.errors import BadRequest

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
        elif req.method == 'PATCH' or (req.method == 'PUT' and
              'X-IVLE-Patch-Semantics' in req.headers_in and
              req.headers_in['X-IVLE-Patch-Semantics'].lower() == 'yes'):
            outjson = self.PATCH(req, cjson.decode(req.read()))
        elif req.method == 'PUT':
            outjson = self.PUT(req, cjson.decode(req.read()))
        else:
            raise BadRequest
        req.content_type = self.content_type
        if outjson is not None:
            req.write(cjson.encode(outjson))
            req.write("\n")
            
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
