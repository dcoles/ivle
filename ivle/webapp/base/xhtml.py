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
import urllib

import genshi.template

from ivle.webapp.media import media_url
from ivle.webapp.core import Plugin as CorePlugin
from ivle.webapp.base.views import BaseView
from ivle.webapp.base.plugins import ViewPlugin, OverlayPlugin
from ivle.webapp.errors import HTTPError, Unauthorized
from ivle.webapp.publisher import NoPath
from ivle.webapp.breadcrumbs import Breadcrumber

class XHTMLView(BaseView):
    """
    A view which provides a base class for views which need to return XHTML
    It is expected that apps which use this view will be written using Genshi
    templates.
    """

    template = 'template.html'
    allow_overlays = True
    breadcrumb_text = None

    def __init__(self, *args, **kwargs):
        super(XHTMLView, self).__init__(*args, **kwargs)

        self.overlay_blacklist = []

        self.plugin_scripts = {}
        self.plugin_styles = {}
        self.scripts_init = []

        self.extra_breadcrumbs = []
        self.overlay_blacklist = []

    def get_context_ancestry(self, req):
        return req.publisher.get_ancestors(self.context)

    def filter(self, stream, ctx):
        return stream

    def render(self, req):
        req.content_type = 'text/html' # TODO: Detect application/xhtml+xml

        # View template
        viewctx = genshi.template.Context()
        self.populate(req, viewctx)

        # The template is found in the directory of the module containing the
        # view.
        app_template = os.path.join(os.path.dirname(
                        inspect.getmodule(self).__file__), self.template) 
        loader = genshi.template.TemplateLoader(".", auto_reload=True)
        tmpl = loader.load(app_template)
        app = self.filter(tmpl.generate(viewctx), viewctx)

        view_scripts = []
        for plugin in self.plugin_scripts:
            for path in self.plugin_scripts[plugin]:
                view_scripts.append(media_url(req, plugin, path))

        view_styles = []
        for plugin in self.plugin_styles:
            for path in self.plugin_styles[plugin]:
                view_styles.append(media_url(req, plugin, path))

        # Global template
        ctx = genshi.template.Context()

        overlay_bits = self.render_overlays(req) if req.user else [[]]*4
        ctx['overlays'] = overlay_bits[0]

        ctx['styles'] = [media_url(req, CorePlugin, 'ivle.css')]
        ctx['styles'] += view_styles
        ctx['styles'] += overlay_bits[1]

        ctx['scripts'] = [media_url(req, CorePlugin, path) for path in
                           ('util.js', 'json2.js', 'md5.js')]
        ctx['scripts'].append(media_url(req, '+external/jquery', 'jquery.js'))
        ctx['scripts'] += view_scripts
        ctx['scripts'] += overlay_bits[2]

        ctx['scripts_init'] = self.scripts_init + overlay_bits[3]
        ctx['app_template'] = app
        ctx['title_img'] = media_url(req, CorePlugin,
                                     "images/chrome/root-breadcrumb.png")
        try:
            ctx['ancestry'] = self.get_context_ancestry(req)
        except NoPath:
            ctx['ancestry'] = []

        # If the view has specified text for a breadcrumb, add one.
        if self.breadcrumb_text:
            ctx['extra_breadcrumbs'] = [ViewBreadcrumb(req, self)]
        else:
            ctx['extra_breadcrumbs'] = []

        # Allow the view to add its own fake breadcrumbs.
        ctx['extra_breadcrumbs'] += self.extra_breadcrumbs

        ctx['crumb'] = Breadcrumber(req).crumb
        self.populate_headings(req, ctx)
        tmpl = loader.load(os.path.join(os.path.dirname(__file__), 
                                                        'ivle-headings.html'))
        req.write(tmpl.generate(ctx).render('xhtml', doctype='xhtml'))
        
    def populate(self, req, ctx):
        raise NotImplementedError()

    def populate_headings(self, req, ctx):
        ctx['favicon'] = None
        ctx['root_dir'] = req.config['urls']['root']
        ctx['public_host'] = req.config['urls']['public_host']
        ctx['svn_base'] = req.config['urls']['svn_addr']
        ctx['write_javascript_settings'] = req.write_javascript_settings
        if req.user:
            ctx['login'] = req.user.login
            ctx['logged_in'] = True
            ctx['nick'] = req.user.nick
        else:
            ctx['login'] = None
            ctx['logged_in'] = False
        ctx['publicmode'] = req.publicmode
        if hasattr(self, 'help'):
            ctx['help_path'] = self.help

        ctx['apps_in_tabs'] = []
        for plugin in req.config.plugin_index[ViewPlugin]:
            if not hasattr(plugin, 'tabs'):
                continue

            for tab in plugin.tabs:
                # tab is a tuple: name, title, desc, icon, path
                new_app = {}
                new_app['this_app'] = hasattr(self, 'tab') \
                                      and tab[0] == self.tab

                # Icon name
                if tab[3] is not None:
                    new_app['has_icon'] = True
                    icon_url = media_url(req, plugin, tab[3])
                    new_app['icon_url'] = icon_url
                    if new_app['this_app']:
                        ctx['favicon'] = icon_url
                else:
                    new_app['has_icon'] = False
                new_app['path'] = req.make_path(tab[4])
                new_app['desc'] = tab[2]
                new_app['name'] = tab[1]
                new_app['weight'] = tab[5]
                ctx['apps_in_tabs'].append(new_app)

        ctx['apps_in_tabs'].sort(key=lambda tab: tab['weight'])

    def render_overlays(self, req):
        """Generate XML streams for the overlays.
        
        Returns a list of streams. Populates the scripts, styles, and 
        scripts_init.
        """
        overlays = []
        styles = []
        scripts = []
        scripts_init = []
        if not self.allow_overlays:
            return (overlays, styles, scripts, scripts_init)

        for plugin in req.config.plugin_index[OverlayPlugin]:
            for overclass in plugin.overlays:
                if overclass in self.overlay_blacklist:
                    continue
                overlay = overclass(req)
                #TODO: Re-factor this to look nicer
                for mplugin in overlay.plugin_scripts:
                    for path in overlay.plugin_scripts[mplugin]:
                        scripts.append(media_url(req, mplugin, path))

                for mplugin in overlay.plugin_styles:
                    for path in overlay.plugin_styles[mplugin]:
                        styles.append(media_url(req, mplugin, path))

                scripts_init += overlay.plugin_scripts_init

                overlays.append(overlay.render(req))
        return (overlays, styles, scripts, scripts_init)

    @classmethod
    def get_error_view(cls, e):
        view_map = {HTTPError:    XHTMLErrorView,
                    Unauthorized: XHTMLUnauthorizedView}
        for exccls in inspect.getmro(type(e)):
            if exccls in view_map:
                return view_map[exccls]

class XHTMLErrorView(XHTMLView):
    template = 'xhtmlerror.html'

    def __init__(self, req, context, lastobj):
        super(XHTMLErrorView, self).__init__(req, context)
        self.lastobj = lastobj

    def get_context_ancestry(self, req):
        return req.publisher.get_ancestors(self.lastobj)

    def populate(self, req, ctx):
        ctx['req'] = req
        ctx['exception'] = self.context

class XHTMLUnauthorizedView(XHTMLErrorView):
    template = 'xhtmlunauthorized.html'

    def __init__(self, req, exception, lastobj):
        super(XHTMLUnauthorizedView, self).__init__(req, exception, lastobj)

        if not req.publicmode and req.user is None:
            # Not logged in. Redirect to login page.
            if req.uri == '/':
                query_string = ''
            else:
                query_string = '?url=' + urllib.quote(req.uri, safe="/~")
            req.throw_redirect('/+login' + query_string)

        req.status = 403

class ViewBreadcrumb(object):
    def __init__(self, req, context):
        self.req = req
        self.context = context

    @property
    def text(self):
        return self.context.breadcrumb_text
