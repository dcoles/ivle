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

# Author: Matt Giuca, Will Grant

"""
This is a mod_python handler program. The correct way to call it is to have
Apache send all requests to be handled by the module 'dispatch'.

Top-level handler. Handles all requests to all pages in IVLE.
Handles authentication (not authorization).
Then passes the request along to the appropriate ivle app.
"""

import sys
import os
import os.path
import urllib
import cgi
import traceback
import logging
import socket
import time
import inspect

import mod_python
import routes

from ivle import util
import ivle.conf
import ivle.conf.apps
from ivle.dispatch.request import Request
from ivle.dispatch import login
from ivle.webapp.base.plugins import ViewPlugin, PublicViewPlugin
from ivle.webapp.errors import HTTPError, Unauthorized
import apps
import html

# XXX List of plugins, which will eventually be read in from conf
plugins_HACK = [
    'ivle.webapp.core#Plugin',
    'ivle.webapp.admin.user#Plugin',
    'ivle.webapp.tutorial#Plugin',
    'ivle.webapp.admin.subject#Plugin',
    'ivle.webapp.filesystem.browser#Plugin',
    'ivle.webapp.filesystem.diff#Plugin',
    'ivle.webapp.filesystem.svnlog#Plugin',
    'ivle.webapp.filesystem.serve#Plugin',
    'ivle.webapp.groups#Plugin',
    'ivle.webapp.console#Plugin',
    'ivle.webapp.security#Plugin',
    'ivle.webapp.media#Plugin',
    'ivle.webapp.forum#Plugin',
    'ivle.webapp.help#Plugin',
    'ivle.webapp.tos#Plugin',
    'ivle.webapp.userservice#Plugin',
] 

def generate_route_mapper(view_plugins, attr):
    """
    Build a Mapper object for doing URL matching using 'routes', based on the
    given plugin registry.
    """
    m = routes.Mapper(explicit=True)
    for plugin in view_plugins:
        # Establish a URL pattern for each element of plugin.urls
        assert hasattr(plugin, 'urls'), "%r does not have any urls" % plugin 
        for url in getattr(plugin, attr):
            routex = url[0]
            view_class = url[1]
            kwargs_dict = url[2] if len(url) >= 3 else {}
            m.connect(routex, view=view_class, **kwargs_dict)
    return m

def get_plugin(pluginstr):
    plugin_path, classname = pluginstr.split('#')
    # Load the plugin module from somewhere in the Python path
    # (Note that plugin_path is a fully-qualified Python module name).
    return (plugin_path,
            getattr(__import__(plugin_path, fromlist=[classname]), classname))

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
        return mod_python.apache.OK

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
        return mod_python.apache.OK

def handler_(req, apachereq):
    """
    Nested handler function. May raise exceptions. The top-level handler is
    just used to catch exceptions.
    Takes both an IVLE request and an Apache req.
    """
    # Hack? Try and get the user login early just in case we throw an error
    # (most likely 404) to stop us seeing not logged in even when we are.
    if not req.publicmode:
        user = login.get_user_details(req)

        # Don't set the user if it is disabled or hasn't accepted the ToS.
        if user and user.valid:
            req.user = user

    ### BEGIN New plugins framework ###
    # XXX This should be done ONCE per Python process, not per request.
    # (Wait till WSGI)
    req.plugins = dict([get_plugin(pluginstr) for pluginstr in plugins_HACK])
    # Index the plugins by base class
    req.plugin_index = {}
    for plugin in req.plugins.values():
        # Getmro returns a tuple of all the super-classes of the plugin
        for base in inspect.getmro(plugin):
            if base not in req.plugin_index:
                req.plugin_index[base] = []
            req.plugin_index[base].append(plugin)
    req.reverse_plugins = dict([(v, k) for (k, v) in req.plugins.items()])

    if req.publicmode:
        req.mapper = generate_route_mapper(req.plugin_index[PublicViewPlugin],
                                           'public_urls')
    else:
        req.mapper = generate_route_mapper(req.plugin_index[ViewPlugin],
                                           'urls')

    matchdict = req.mapper.match(req.uri)
    if matchdict is not None:
        viewcls = matchdict['view']
        # Get the remaining arguments, less 'view', 'action' and 'controller'
        # (The latter two seem to be built-in, and we don't want them).
        kwargs = matchdict.copy()
        del kwargs['view']
        try:
            # Instantiate the view, which should be a BaseView class
            view = viewcls(req, **kwargs)

            # Check that the request (mainly the user) is permitted to access
            # the view.
            if not view.authorize(req):
                raise Unauthorized()
            # Render the output
            view.render(req)
        except HTTPError, e:
            # A view explicitly raised an HTTP error. Respect it.
            req.status = e.code

            # Try to find a custom error view.
            if hasattr(viewcls, 'get_error_view'):
                errviewcls = viewcls.get_error_view(e)
            else:
                errviewcls = None

            if errviewcls:
                errview = errviewcls(req, e)
                errview.render(req)
                return req.OK
            elif e.message:
                req.write(e.message)
                return req.OK
            else:
                return e.code
        except Exception, e:
            # A non-HTTPError appeared. We have an unknown exception. Panic.
            handle_unknown_exception(req, *sys.exc_info())
            return req.OK
        else:
            req.store.commit()
            return req.OK
    ### END New plugins framework ###

    # Check req.app to see if it is valid. 404 if not.
    if req.app is not None and req.app not in ivle.conf.apps.app_url:
        req.throw_error(Request.HTTP_NOT_FOUND,
            "There is no application called %s." % repr(req.app))

    # Special handling for public mode - only allow the public app, call it
    # and get out.
    # NOTE: This will not behave correctly if the public app uses
    # write_html_head_foot, but "serve" does not.
    if req.publicmode:
        if req.app != ivle.conf.apps.public_app:
            req.throw_error(Request.HTTP_FORBIDDEN,
                "This application is not available on the public site.")
        app = ivle.conf.apps.app_url[ivle.conf.apps.public_app]
        apps.call_app(app.dir, req)
        return req.OK

    # app is the App object for the chosen app
    if req.app is None:
        app = ivle.conf.apps.app_url[ivle.conf.apps.default_app]
    else:
        app = ivle.conf.apps.app_url[req.app]

    # Check if app requires auth. If so, perform authentication and login.
    # This will either return a User object, None, or perform a redirect
    # which we will not catch here.
    if app.requireauth:
        logged_in = req.user is not None
    else:
        logged_in = True

    assert logged_in # XXX

    if logged_in:
        # Keep the user's session alive by writing to the session object.
        # req.get_session().save()
        # Well, it's a fine idea, but it creates considerable grief in the
        # concurrent update department, so instead, we'll just make the
        # sessions not time out.
        req.get_session().unlock()

        # If user did not specify an app, HTTP redirect to default app and
        # exit.
        if req.app is None:
            req.throw_redirect(util.make_path(ivle.conf.apps.default_app))

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
    logfile = os.path.join(ivle.conf.log_path, 'ivle_error.log')
    logfail = False
    # For some reason, some versions of mod_python have "_server" instead of
    # "main_server". So we check for both.
    try:
        admin_email = mod_python.apache.main_server.server_admin
    except AttributeError:
        try:
            admin_email = mod_python.apache._server.server_admin
        except AttributeError:
            admin_email = ""
    try:
        httpcode = exc_value.httpcode
        req.status = httpcode
    except AttributeError:
        httpcode = None
        req.status = mod_python.apache.HTTP_INTERNAL_SERVER_ERROR
    try:
        publicmode = req.publicmode
    except AttributeError:
        publicmode = True
    try:
        login = req.user.login
    except AttributeError:
        login = None
    try:
        role = req.user.role
    except AttributeError:
        role = None

    # Log File
    try:
        for h in logging.getLogger().handlers:
            logging.getLogger().removeHandler(h)
        logging.basicConfig(level=logging.INFO,
            format='%(asctime)s %(levelname)s: ' +
                '(HTTP: ' + str(req.status) +
                ', Ref: ' + str(login) + '@' +
                str(socket.gethostname()) + str(req.uri) +
                ') %(message)s',
            filename=logfile,
            filemode='a')
    except IOError:
        logfail = True
    logging.debug('Logging Unhandled Exception')

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
        req.write_javascript_settings = False
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
        
        # Logging
        logging.info(str(msg))
        
        req.write("<p>(HTTP error code %d)</p>\n" % httpcode)
        if logfail:
            req.write("<p>Warning: Could not open Error Log: '%s'</p>\n"
                %cgi.escape(logfile))
        req.write('</div>\n')
        html.write_html_foot(req)
    else:
        # A "bad" error message. We shouldn't get here unless IVLE
        # misbehaves (which is currently very easy, if things aren't set up
        # correctly).
        # Write the traceback.
        # If this is a non-4xx IVLEError, get the message and httpcode and
        # make the error message a bit nicer (but still include the
        # traceback).
        # We also need to special-case IVLEJailError, as we can get another
        # almost-exception out of it.

        codename, msg = None, None

        if exc_type is util.IVLEJailError:
            msg = exc_value.type_str + ": " + exc_value.message
            tb = 'Exception information extracted from IVLEJailError:\n'
            tb += urllib.unquote(exc_value.info)
        else:
            try:
                codename, msg = req.get_http_codename(httpcode)
            except AttributeError:
                pass
            # Override the default message with the supplied one,
            # if available.
            if hasattr(exc_value, 'message') and exc_value.message is not None:
                msg = exc_value.message
                # Prepend the exception type
                if exc_type != util.IVLEError:
                    msg = exc_type.__name__ + ": " + msg

            tb = ''.join(traceback.format_exception(exc_type, exc_value,
                                                    exc_traceback))

        # Logging
        logging.error('%s\n%s'%(str(msg), tb))
        # Error messages are only displayed is the user is NOT a student,
        # or if there has been a problem logging the error message
        show_errors = (not publicmode) and ((login and \
                            str(role) != "student") or logfail)
        req.write("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"                 
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">                                      
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>IVLE Internal Server Error</title></head>
<body>
<h1>IVLE Internal Server Error""")
        if (show_errors):
            if (codename is not None
                        and httpcode != mod_python.apache.HTTP_INTERNAL_SERVER_ERROR):
                req.write(": %s" % cgi.escape(codename))
        
        req.write("""</h1>
<p>An error has occured which is the fault of the IVLE developers or
administration. The developers have been notified.</p>
""")
        if (show_errors):
            if msg is not None:
                req.write("<p>%s</p>\n" % cgi.escape(msg))
            if httpcode is not None:
                req.write("<p>(HTTP error code %d)</p>\n" % httpcode)
            req.write("""
    <p>Please report this to <a href="mailto:%s">%s</a> (the system
    administrator). Include the following information:</p>
    """ % (cgi.escape(admin_email), cgi.escape(admin_email)))

            req.write("<pre>\n%s\n</pre>\n"%cgi.escape(tb))
            if logfail:
                req.write("<p>Warning: Could not open Error Log: '%s'</p>\n"
                    %cgi.escape(logfile))
        req.write("</body></html>")
