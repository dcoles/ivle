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

# Author: Matt Giuca

import inspect
import os.path

import genshi.template

from ivle.webapp.base.views import BaseView
from ivle.webapp.base.xhtml import GenshiLoaderMixin


class TextView(GenshiLoaderMixin, BaseView):
    """
    A view which provides a base class for views which need to return plain
    text results using Genshi text templates.
    """

    template = 'template.txt'
    content_type = 'text/plain'

    def get_context_ancestry(self, req):
        return req.publisher.get_ancestors(self.context)

    def filter(self, stream, ctx):
        return stream

    def render(self, req):
        req.content_type = self.content_type

        # View template
        viewctx = genshi.template.Context()
        self.populate(req, viewctx)

        # The template is found in the directory of the module containing the
        # view.
        app_template = os.path.join(os.path.dirname(
                        inspect.getmodule(self).__file__), self.template) 
        tmpl = self._loader.load(app_template,
                                 cls=genshi.template.text.NewTextTemplate)
        app = self.filter(tmpl.generate(viewctx), viewctx)

        self.populate_headings(req, viewctx)
        req.write(tmpl.generate(viewctx).render())

    def populate(self, req, ctx):
        raise NotImplementedError()

    def populate_headings(self, req, ctx):
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
