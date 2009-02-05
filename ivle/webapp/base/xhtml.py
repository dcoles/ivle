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

import inspect
import os.path

import genshi.template

from ivle.webapp.base.views import BaseView
import ivle.conf
import ivle.util

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
