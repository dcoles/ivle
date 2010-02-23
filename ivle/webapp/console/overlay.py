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

from ivle.webapp.base.overlays import XHTMLOverlay
from ivle.webapp.media import media_url
from ivle.webapp.core import Plugin as CorePlugin

class ConsoleOverlay(XHTMLOverlay):
    template = 'overlay.html'
    
    plugin_scripts = {'ivle.webapp.console': ['console.js']}
    plugin_styles  = {'ivle.webapp.console': ['console.css']}
    plugin_scripts_init = ['console_init']
    
    def populate(self, req, ctx):
        ctx['windowpane'] = True
        ctx['maximize_path'] = media_url(req, CorePlugin, 
                                         'images/interface/maximize.png')
        ctx['minimize_path'] = media_url(req, CorePlugin, 
                                         'images/interface/minimize.png')
        ctx['start_body_attrs'] = {'class': 'console_body windowpane minimal'}
        return ctx
