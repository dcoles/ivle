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

# App: subjects
# Author: Matt Giuca
# Date: 29/2/2008

# This is an IVLE application.
# A sample / testing application for IVLE.

import cgi
import urllib

from ivle import util
from ivle.conf import apps

def handle(req):
    """Handler for the student home application.
    Links everywhere else and displays system-wide messages."""

    req.content_type = "text/html"
    req.write_html_head_foot = True     # Have dispatch print head and foot

    req.write("""<div id="ivle_padding">
  <h2>IVLE Home: %s</h2>
""" % cgi.escape(req.user.nick))

    req.write("""<h3>Subjects</h3>
""")
    # TODO

    req.write("""<h3>IVLE Apps</h3>
  <p>These are the different facilities provided by IVLE.
    They are always accessible from the links at the top.</p>
  <ul>
""")
    for app in apps.apps_on_home_page:
        req.write('    <li><a href="%s">%s</a><br />\n      %s</li>\n'
        % (
            urllib.quote(util.make_path(app)),
            cgi.escape(apps.app_url[app].name),
            cgi.escape(apps.app_url[app].desc),
        ))
    req.write("  </ul>\n")

    req.write("""<h3>Announcements</h3>
""")
    # TODO

    req.write("</div>\n")
