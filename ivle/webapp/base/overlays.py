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

# Author: Nick Chadwick, Will Grant

import os
import inspect

import genshi

class BaseOverlay(object):
    """Abstract base class for all overlays."""
    plugin_scripts = {}
    plugin_styles = {}
    plugin_scripts_init = []
    def __init__(self, req):
        self.req = req

    def render(self, req):
        raise NotImplementedError()
        
class XHTMLOverlay(BaseOverlay):
    """Abstract base class for XHTML overlays.
    
    An overlay which provides a base class for overlays which need to return 
    XHTML. It is expected that apps which use this overlay will be written using
    Genshi templates.
    """
    
    template = 'template.html'
    
    def render(self, req):
        """Renders an XML stream from the template for this overlay."""
        ctx = genshi.template.Context()
        # This is where the sub-class is actually called
        self.populate(req, ctx)
        
        # Renders out the template.
        template_path = os.path.join(os.path.dirname(
                        inspect.getmodule(self).__file__), self.template)
        loader = genshi.template.TemplateLoader(".", auto_reload=True)
        tmpl = loader.load(template_path)
        return tmpl.generate(ctx)
        
    def populate(self, req, ctx):
        raise NotImplementedError()
