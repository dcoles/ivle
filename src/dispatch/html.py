# IVLE - Informatics Virtual Learning Environment
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

# Module: dispatch.html
# Author: Matt Giuca
# Date: 12/12/2007

# Provides functions for writing the dispatch-generated HTML header and footer
# content (the common parts of the HTML pages shared across the entire site).
# Does not include the login page. See login.py.

import conf
import conf.apps
from common import util

def write_html_head(req):
    """Writes the HTML header, given a request object.

    req: An IVLE request object. Reads attributes such as title. Also used to
    write to."""

    # Write the XHTML opening and head element
    if req.title != None:
        titlepart = ' - ' + req.title
    else:
        titlepart = ''
    req.write("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>IVLE%s</title>
  <meta http-equiv="Content-Type"
    content="%s"; charset=utf-8" />
</head>

""" % (titlepart, req.content_type))

    # Open the body element and write a bunch of stuff there (the header)
    req.write("""<body>
<h1>IVLE - Informatics Virtual Learning Environment</h1>
""")
    print_apps_list(req)

def write_html_foot(req):
    """Writes the HTML footer, given a request object.

    req: An IVLE request object. Written to.
    """
    req.write("</body>\n</html>\n")

def print_apps_list(file):
    """Prints all app tabs, as a UL. Prints a list item for each app that has
    a tab.

    file: Object with a "write" method - ie. the request object.
    Reads from: conf
    """
    file.write('<ul class="apptabs">\n')

    for urlname in conf.apps.apps_in_tabs:
        app = conf.apps.app_url[urlname]
        file.write('  <li><a href="%s">%s</a></li>\n'
            % (util.make_path(app.dir), app.name))

    file.write('</ul>\n')
