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

import cgi
import os.path

from ivle import util

def write_html_head(req):
    """Writes the HTML header, given a request object.

    req: An IVLE request object. Reads attributes such as title. Also used to
    write to."""

    # Write the XHTML opening and head element
    # Note the inline JavaScript, which provides the client with constants
    # derived from the server configuration.
    if req.title != None:
        titlepart = req.title + ' - '
    else:
        titlepart = ''
    req.write("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>%sIVLE</title>
  <meta http-equiv="Content-Type" content="%s; charset=utf-8" />
""" % (cgi.escape(titlepart), cgi.escape(req.content_type)))

    req.write("""  <link rel="stylesheet" type="text/css" href="%s" />
""" % cgi.escape(util.make_path('+media/ivle.webapp.core/ivle.css')))

    req.write("</head>\n\n")

    # Open the body element and write a bunch of stuff there (the header)
    req.write("""<body>
<div id="ivleheader"></div>
<div id="ivleheader_text">
  <h1>IVLE</h1>
  <h2>Informatics Virtual Learning Environment</h2>
""")

    if req.publicmode:
        req.write('   <p class="userhello">Running in public mode.</p>')
    elif req.user:
        # Get the user's nickname from the request session
        nickname = req.user.nick
        req.write('  <p class="userhello"><span id="usernick">%s</span> '
            '(<span class="username">%s</span>) |\n'
            '    <a href="%s">Settings</a> |\n'
            '    <a href="%s">Help</a> |\n'
            '    <a href="%s">Sign out</a>\n'
            '  </p>\n' %
            (cgi.escape(nickname), cgi.escape(req.user.login),
             cgi.escape(util.make_path(
                        os.path.join('~' + req.user.login, '+settings'))),
             cgi.escape(util.make_path('+help')),
             cgi.escape(util.make_path('+logout'))))
    else:
        req.write('  <p class="userhello">Not logged in.</p>')

    req.write('</div>\n<div id="ivleheader_tabs">\n')
    req.write('</div>\n<div id="ivlebody">\n')

def write_html_foot(req):
    """Writes the HTML footer, given a request object.

    req: An IVLE request object. Written to.
    """
    req.write("</div>\n</body>\n</html>\n")
