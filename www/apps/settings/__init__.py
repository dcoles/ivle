# IVLE
# Copyright (C) 2007-2008 The University of Melbourne
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

# App: settings
# Author: Matt Giuca
# Date: 25/2/2008

# User settings UI
# (Also provides UI for administering users, given sufficient privileges).

from ivle import util

import genshi
import genshi.template

def handle(req):
    """Handler for the Settings application."""

    # Set request attributes
    req.content_type = "text/html"
    # These files don't really exist - just a test of our linking
    # capabilities
    req.styles = [
        "media/settings/settings.css",
    ]
    req.scripts = [
        "media/settings/settings.js",
        "media/common/json2.js",
        "media/common/util.js",
    ]
    req.scripts_init = [
        "revert_settings"
    ]
    req.write_html_head_foot = True     # Have dispatch print head and foot

    loader = genshi.template.TemplateLoader(".", auto_reload=True)
    tmpl = loader.load(util.make_local_path("apps/settings/template.html"))
    req.write(tmpl.generate().render('html')) #'xhtml', doctype='xhtml'))
