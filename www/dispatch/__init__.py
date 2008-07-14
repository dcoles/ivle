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

import sys
import os
import os.path
import conf
import conf.apps
import apps

from request import Request
import html
import cgi
import login
from common import (util, forumutil)
import traceback

def handler(req):
    """Handles a request which may be to anywhere in the site except media.
    Intended to be called by mod_python, as a handler.

    req: An Apache request object.
    """
    # Make the request object into an IVLE request which can be passed to apps
    apachereq = req
    try:
        req = Request(req, html.write_html_head)
    except Exception:
        # Pass the apachereq to error reporter, since ivle req isn't created
        # yet.
        handle_unknown_exception(apachereq, *sys.exc_info())
        # Tell Apache not to generate its own errors as well
        return apache.OK

    # Run the main handler, and catch all exceptions
    try:
        return handler_(req, apachereq)
    except mod_python.apache.SERVER_RETURN:
        # An apache error. We discourage these, but they might still happen.
        # Just raise up.
        raise
    except Exception:
        handle_unknown_exception(req, *sys.exc_info())
        # Tell Apache not to generate its own errors as well
        return apache.OK

def handler_(req, apachereq):
    """
    Nested handler function. May raise exceptions. The top-level handler is
    just used to catch exceptions.
    Takes both an IVLE request and an Apache req.
    """
    # Check req.app to see if it is valid. 404 if not.
    if req.app is not None and req.app not in conf.apps.app_url:
        # Maybe it is a special app!
        if req.app == 'logout':
            logout(req)
        else:
            req.throw_error(Request.HTTP_NOT_FOUND,
                "There is no application called %s." % repr(req.app))

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
    # This will either return a User object, None, or perform a redirect
    # which we will not catch here.
    if app.requireauth:
        req.user = login.login(req)
        logged_in = req.user is not None
    else:
        req.user = login.get_user_details(req)
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
    req.add_cookie(forumutil.invalidated_forum_cookie())
    req.throw_redirect(util.make_path(''))

def handle_unknown_exception(req, exc_type, exc_value, exc_traceback):
    """
    Given an exception that has just been thrown from IVLE, print its details
    to the request.
    This is a full handler. It assumes nothing has been written, and writes a
    complete HTML page.
    req: May be EITHER an IVLE req or an Apache req.
    IVLE reqs may have the HTML head/foot written (on a 400 error), but
    the handler code may pass an apache req if an exception occurs before
    the IVLE request is created.
    """
    req.content_type = "text/html"
    # For some reason, some versions of mod_python have "_server" instead of
    # "main_server". So we check for both.
    try:
        admin_email = apache.main_server.server_admin
    except AttributeError:
        try:
            admin_email = apache._server.server_admin
        except AttributeError:
            admin_email = ""
    try:
        httpcode = exc_value.httpcode
        req.status = httpcode
    except AttributeError:
        httpcode = None
        req.status = apache.HTTP_INTERNAL_SERVER_ERROR
    # We handle 3 types of error.
    # IVLEErrors with 4xx response codes (client error).
    # IVLEErrors with 5xx response codes (handled server error).
    # Other exceptions (unhandled server error).
    # IVLEErrors should not have other response codes than 4xx or 5xx
    # (eg. throw_redirect should have been used for 3xx codes).
    # Therefore, that is treated as an unhandled error.

    if (exc_type == util.IVLEError and httpcode >= 400
        and httpcode <= 499):
        # IVLEErrors with 4xx response codes are client errors.
        # Therefore, these have a "nice" response (we even coat it in the IVLE
        # HTML wrappers).
        req.write_html_head_foot = True
        req.write('<div id="ivle_padding">\n')
        try:
            codename, msg = req.get_http_codename(httpcode)
        except AttributeError:
            codename, msg = None, None
        # Override the default message with the supplied one,
        # if available.
        if exc_value.message is not None:
            msg = exc_value.message
        if codename is not None:
            req.write("<h1>Error: %s</h1>\n" % cgi.escape(codename))
        else:
            req.write("<h1>Error</h1>\n")
        if msg is not None:
            req.write("<p>%s</p>\n" % cgi.escape(msg))
        else:
            req.write("<p>An unknown error occured.</p>\n")
        req.write("<p>(HTTP error code %d)</p>\n" % httpcode)
        req.write('</div>\n')
    else:
        # A "bad" error message. We shouldn't get here unless IVLE
        # misbehaves (which is currently very easy, if things aren't set up
        # correctly).
        # Write the traceback.
        # If this is a non-4xx IVLEError, get the message and httpcode and
        # make the error message a bit nicer (but still include the
        # traceback).
        try:
            codename, msg = req.get_http_codename(httpcode)
        except AttributeError:
            codename, msg = None, None
        # Override the default message with the supplied one,
        # if available.
        if hasattr(exc_value, 'message') and exc_value.message is not None:
            msg = exc_value.message
            # Prepend the exception type
            if exc_type != util.IVLEError:
                msg = exc_type.__name__ + ": " + msg

        tb = ''.join(traceback.format_exception(exc_type, exc_value,
                                                exc_traceback))

        req.write("""<html>
<head><title>IVLE Internal Server Error</title></head>
<body>
<h1>IVLE Internal Server Error""")
        if (codename is not None
            and httpcode != apache.HTTP_INTERNAL_SERVER_ERROR):
            req.write(": %s" % cgi.escape(codename))
        req.write("""</h1>
<p>An error has occured which is the fault of the IVLE developers or
administration.</p>
""")
        if msg is not None:
            req.write("<p>%s</p>\n" % cgi.escape(msg))
        if httpcode is not None:
            req.write("<p>(HTTP error code %d)</p>\n" % httpcode)
        req.write("""
<p>Please report this to <a href="mailto:%s">%s</a> (the system
administrator). Include the following information:</p>
""" % (cgi.escape(admin_email), cgi.escape(admin_email)))

        req.write("<pre>\n")
        req.write(cgi.escape(tb))
        req.write("</pre>\n</body>\n")
