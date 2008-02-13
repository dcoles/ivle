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

# Module: dispatch
# Author: Matt Giuca
# Date: 11/12/2007

# This is a mod_python handler program. The correct way to call it is to have
# Apache send all requests to be handled by the module 'dispatch'.

# Top-level handler. Handles all requests to all pages in IVLE.
# Handles authentication (not authorization).
# Then passes the request along to the appropriate ivle app.

import mod_python
from mod_python import apache

import os
import os.path
import conf
import conf.apps
import apps

from request import Request
import html
import login
from common import util

def handler(req):
    """Handles a request which may be to anywhere in the site except media.
    Intended to be called by mod_python, as a handler.

    req: An Apache request object.
    """
    # Make the request object into an IVLE request which can be passed to apps
    apachereq = req
    req = Request(req, html.write_html_head)

    # Check req.app to see if it is valid. 404 if not.
    if req.app is not None and req.app not in conf.apps.app_url:
        # Maybe it is a special app!
        if req.app == 'logout':
            logout(req)
        else:
            # TODO: Nicer 404 message?
            req.throw_error(Request.HTTP_NOT_FOUND)

    # Special handling for public mode - just call public app and get out
    # NOTE: This will not behave correctly if the public app uses
    # write_html_head_foot, but "serve" does not.
    if req.publicmode:
        app = conf.apps.app_url[conf.apps.public_app]
        apps.call_app(app.dir, req)
        return req.OK

    # app is the App object for the chosen app
    if req.app is None:
        app = conf.apps.app_url[conf.apps.default_app]
    else:
        app = conf.apps.app_url[req.app]

    # Check if app requires auth. If so, perform authentication and login.
    if app.requireauth:
        req.username = login.login(req)
        logged_in = req.username is not None
    else:
        req.username = login.get_username(req)
        logged_in = True

    if logged_in:
        # Keep the user's session alive by writing to the session object.
        # req.get_session().save()
        # Well, it's a fine idea, but it creates considerable grief in the
        # concurrent update department, so instead, we'll just make the
        # sessions not time out.
        
        # If user did not specify an app, HTTP redirect to default app and
        # exit.
        if req.app is None:
            req.throw_redirect(util.make_path(conf.apps.default_app))

        # Set the default title to the app's tab name, if any. Otherwise URL
        # name.
        if app.name is not None:
            req.title = app.name
        else:
            req.title = req.app

        # Call the specified app with the request object
        apps.call_app(app.dir, req)
    # if not logged in, login.login will have written the login box.
    # Just clean up and exit.

    # MAKE SURE we write the HTTP (and possibly HTML) header. This
    # wouldn't happen if nothing else ever got written, so we have to make
    # sure.
    req.ensure_headers_written()

    # When done, write out the HTML footer if the app has requested it
    if req.write_html_head_foot:
        html.write_html_foot(req)

    # Note: Apache will not write custom HTML error messages here.
    # Use req.throw_error to do that.
    return req.OK

def logout(req):
    """Log out the current user (if any) by destroying the session state.
    Then redirect to the top-level IVLE page."""
    session = req.get_session()
    session.invalidate()
    session.delete()
    req.throw_redirect(util.make_path(''))
