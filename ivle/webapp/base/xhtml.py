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

from ivle.webapp.media import media_url
from ivle.webapp.core import Plugin as CorePlugin
from ivle.webapp.base.views import BaseView
from ivle.webapp.base.plugins import OverlayPlugin
from ivle.webapp.errors import HTTPError, Unauthorized
import ivle.conf
import ivle.util

class XHTMLView(BaseView):
    """
    A view which provides a base class for views which need to return XHTML
    It is expected that apps which use this view will be written using Genshi
    templates.
    """

    template = 'template.html'
    plugin_scripts = {}
    plugin_styles = {}
    overlay_blacklist = []

    def __init__(self, req, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def render(self, req):
        req.content_type = 'text/html' # TODO: Detect application/xhtml+xml

        # View template
        viewctx = genshi.template.Context()
        self.populate(req, viewctx)

        # The template is found in the directory of the module containing the
        # view.
        app_template = os.path.join(os.path.dirname(
                        inspect.getmodule(self).__file__), self.template) 
        req.write_html_head_foot = False
        loader = genshi.template.TemplateLoader(".", auto_reload=True)
        tmpl = loader.load(app_template)
        app = tmpl.generate(viewctx)

        for plugin in self.plugin_scripts:
            for path in self.plugin_scripts[plugin]:
                req.scripts.append(media_url(req, plugin, path))

        for plugin in self.plugin_styles:
            for path in self.plugin_styles[plugin]:
                req.styles.append(media_url(req, plugin, path))

        # Global template
        ctx = genshi.template.Context()
        # XXX: Leave this here!! (Before req.styles is read)
        ctx['overlays'] = self.render_overlays(req)

        ctx['styles'] = [media_url(req, CorePlugin, 'ivle.css')]
        ctx['styles'] += req.styles

        ctx['scripts'] = [media_url(req, CorePlugin, path) for path in
                           ('util.js', 'json2.js', 'md5.js', 'tos.js')]
        ctx['scripts'] += req.scripts

        ctx['scripts_init'] = req.scripts_init
        ctx['app_template'] = app
        self.populate_headings(req, ctx)
        tmpl = loader.load(os.path.join(os.path.dirname(__file__), 
                                                        'ivle-headings.html'))
        req.write(tmpl.generate(ctx).render('xhtml', doctype='xhtml'))
        
    def populate(self, req, ctx):
        raise NotImplementedError()

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
            ctx['logged_in'] = False
        ctx['publicmode'] = req.publicmode
        ctx['apps_in_tabs'] = []
        if hasattr(self, 'help'):
            ctx['help_path'] = self.help
        for urlname in ivle.conf.apps.apps_in_tabs:
            new_app = {}
            app = ivle.conf.apps.app_url[urlname]
            new_app['this_app'] = hasattr(self, 'appname') \
                                  and urlname == self.appname
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
            
    def render_overlays(self, req):
        """Generate XML streams for the overlays.
        
        Returns a list of streams. Populates the scripts, styles, and 
        scripts_init.
        """
        overlays = []
        for plugin in req.plugin_index[OverlayPlugin]:
            for overclass in plugin.overlays:
                if overclass in self.overlay_blacklist:
                    continue
                overlay = overclass(req)
                #TODO: Re-factor this to look nicer
                for mplugin in overlay.plugin_scripts:
                    for path in overlay.plugin_scripts[mplugin]:
                        req.scripts.append(media_url(req, mplugin, path))

                for mplugin in overlay.plugin_styles:
                    for path in overlay.plugin_styles[mplugin]:
                        req.styles.append(media_url(req, mplugin, path))

                req.scripts_init += overlay.plugin_scripts_init

                overlays.append(overlay.render(req))
        return overlays

    @classmethod
    def get_error_view(cls, e):
        view_map = {HTTPError:    XHTMLErrorView,
                    Unauthorized: XHTMLUnauthorizedView}
        for exccls in inspect.getmro(type(e)):
            if exccls in view_map:
                return view_map[exccls]

class XHTMLErrorView(XHTMLView):
    template = 'xhtmlerror.html'

    def __init__(self, req, exception):
        self.context = exception

    def populate(self, req, ctx):
        ctx['exception'] = self.context

class XHTMLUnauthorizedView(XHTMLErrorView):
    template = 'xhtmlunauthorized.html'

    def __init__(self, req, exception):
        super(XHTMLUnauthorizedView, self).__init__(req, exception)
        if req.user is None:
            # Not logged in. Redirect to login page.
            req.throw_redirect('/') # XXX: Need proper URL.

        req.status = 403
