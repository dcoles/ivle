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

import conf
import conf.apps
from common import util

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
    # Write inline JavaScript which gives the client code access to certain
    # server-side variables.
    if req.user:
        username = repr(req.user.login)
    else:
        username = "null"
    req.write("""  <script type="text/javascript">
    root_dir = %s;
    username = %s;
  </script>
""" % (repr(conf.root_dir), username))
    iconurl = get_icon_url(req.app)
    if iconurl:
        req.write("""  <link rel="shortcut icon" href="%s" />
""" % cgi.escape(iconurl))
    req.write("""  <link rel="stylesheet" type="text/css" href="%s" />
""" % cgi.escape(util.make_path('media/common/ivle.css')))

    # Write any app-specific style and script links
    for style in req.styles:
        req.write('  <link rel="stylesheet" type="text/css" href="%s" />\n'
            % cgi.escape(util.make_path(style)))
    for script in req.scripts:
        req.write('  <script type="text/javascript" src="%s"></script>\n'
            % cgi.escape(util.make_path(script)))

    req.write("</head>\n\n")

    # Open the body element and write a bunch of stuff there (the header)
    req.write("""<body>
<div id="ivleheader"></div>
<div id="ivleheader_text">
  <h1>IVLE</h1>
  <h2>Informatics Virtual Learning Environment</h2>
""")

    if req.user:
        # Get the user's nickname from the request session
        nickname = req.user.nick
        req.write('  <p class="userhello">%s (<span '
            'class="username">%s</span>) |\n'
            '    <a href="%s">Help</a> |\n'
            '    <a href="%s">Logout</a>\n'
            '  </p>\n' %
            (cgi.escape(nickname), cgi.escape(req.user.login),
             cgi.escape(get_help_url(req)),
             cgi.escape(util.make_path('logout'))))
    else:
        req.write('  <p class="userhello">Not logged in.</p>')

    # ivleheader_tabs is a separate div, so it can be positioned absolutely
    req.write('</div>\n<div id="ivleheader_tabs">\n')

    # If the "debuginfo" app is installed, display a warning to the admin to
    # make sure it is removed in production.
    if "debuginfo" in conf.apps.app_url:
        req.write("  <p><small>Warning: debuginfo is enabled. Remove this "
            "app from conf.apps.app_url when placed into production."
            "</small></p>\n")

    # If req has a "no_agreement" attribute, then it is because the user has
    # not signed the agreement; therefore we are displaying the TOS page.
    # Do not show apps (see dispatch.login).
    if req.user and not req.user.state == 'no_agreement':
        # Only print app tabs if logged in
        print_apps_list(req, req.app)
    req.write('</div>\n<div id="ivlebody">\n')

def write_html_foot(req):
    """Writes the HTML footer, given a request object.

    req: An IVLE request object. Written to.
    """
    req.write("</div>\n</body>\n</html>\n")

def get_help_url(req):
    """Gets the help URL most relevant to this page, to place as the
    "help" link at the top of the page."""
    reqapp = req.app if hasattr(req, 'app') else None
    if reqapp == 'help':
        # We're already in help. Link to the exact current page
        # instead of the generic help page.
        return req.uri
    if reqapp is not None and conf.apps.app_url[reqapp].hashelp:
        help_path = os.path.join('help', reqapp)
    else:
        help_path = 'help'
    return util.make_path(help_path)

def get_icon_url(appurl, small=False):
    """Given an app's url name, gets the URL of the icon image for this app,
    relative to the site root. Returns None if the app has no icon."""
    if appurl is None: return None
    app = conf.apps.app_url[appurl]
    if small:
        icon_dir = conf.apps.app_icon_dir_small
    else:
        icon_dir = conf.apps.app_icon_dir
    if app.icon is None: return None
    return util.make_path(os.path.join(icon_dir, app.icon))

def print_apps_list(file, thisapp):
    """Prints all app tabs, as a UL. Prints a list item for each app that has
    a tab.

    file: Object with a "write" method - ie. the request object.
    Reads from: conf
    """
    file.write('  <ul id="apptabs">\n')

    for urlname in conf.apps.apps_in_tabs:
        app = conf.apps.app_url[urlname]
        if urlname == thisapp:
            li_attr = ' class="thisapp"'
        else:
            li_attr = ''
        file.write('    <li%s>' % li_attr)
        if app.icon:
            file.write('<img src="%s" alt="" /> '
                % cgi.escape(get_icon_url(urlname)))
        file.write('<a href="%s">%s</a></li>\n'
            % (cgi.escape(util.make_path(urlname)), cgi.escape(app.name)))

    file.write('  </ul>\n')
