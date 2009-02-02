# IVLE
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

# App: Logout
# Author: Nick Chadwick
# Date: 13/01/2009

from ivle import util

import genshi
import genshi.template

# url path for this app
THIS_APP = "logout"

def handle(req):
    if req.method == "POST":
        req.logout()
    else:
        req.content_type = "text/html"
        req.write_html_head_foot = True
        ctx = genshi.template.Context()
        ctx['path'] =  util.make_path('logout')
        loader = genshi.template.TemplateLoader(".", auto_reload=True)
        tmpl = loader.load(util.make_local_path("apps/logout/template.html"))
        req.write(tmpl.generate(ctx).render('html')) #'xhtml', doctype='xhtml'))
