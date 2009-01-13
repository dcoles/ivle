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

import cgi
from ivle import util

# url path for this app
THIS_APP = "logout"

def handle(req):
    if req.method == "POST":
        req.logout()
    else:
        req.write_html_head_foot = True
        req.content_type = "text/html"
        req.write('<div id="ivle_padding">\n'
                  '<h3>Are you sure you want to logout?</h3><p>'
                  '<form action="%s" method="POST">\n'
                  '    <input type="submit" value="Logout" />\n'
                  '</form>\n</div>\n' % (cgi.escape(util.make_path('logout'))))
