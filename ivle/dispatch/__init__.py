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
Handles authentication and delegates to views for authorization,
then passes the request along to the appropriate view.
"""

import sys
import os
import os.path
import urllib
import urlparse
import cgi
import traceback
import logging
import socket
import time

import mod_python

from ivle import util
import ivle.config
from ivle.dispatch.request import Request
import ivle.webapp.security
from ivle.webapp.base.plugins import ViewPlugin, PublicViewPlugin
from ivle.webapp.base.xhtml import XHTMLView, XHTMLErrorView
from ivle.webapp.errors import BadRequest, HTTPError, NotFound, Unauthorized
from ivle.webapp.publisher import Publisher, PublishingError
from ivle.webapp import ApplicationRoot

config = ivle.config.Config()

class ObjectPermissionCheckingPublisher(Publisher):
    """A specialised publisher that checks object permissions.

    This publisher verifies that the user holds any permission at all
    on the model objects through which the resolution path passes. If
    no permission is held, resolution is aborted with an Unauthorized
    exception.

    IMPORTANT: This does NOT check view permissions. It only checks
    the objects in between the root and the view, exclusive!
    """

    def traversed_to_object(self, obj):
        """Check that the user has any permission at all over the object."""
        if (hasattr(obj, 'get_permissions') and
            len(obj.get_permissions(self.root.user, config)) == 0):
            # Indicate the forbidden object if this is an admin.
            if self.root.user and self.root.user.admin:
                raise Unauthorized('Unauthorized: %s' % obj)
            else:
                raise Unauthorized()


def generate_publisher(view_plugins, root, publicmode=False):
    """
    Build a Mapper object for doing URL matching using 'routes', based on the
    given plugin registry.
    """
    r = ObjectPermissionCheckingPublisher(root=root)

    r.add_set_switch('api', 'api')

    if publicmode:
        view_attr = 'public_views'
        forward_route_attr = 'public_forward_routes'
        reverse_route_attr = 'public_reverse_routes'
    else:
        view_attr = 'views'
        forward_route_attr = 'forward_routes'
        reverse_route_attr = 'reverse_routes'


    for plugin in view_plugins:
        if hasattr(plugin, forward_route_attr):
            for fr in getattr(plugin, forward_route_attr):
                # An annotated function can also be passed in directly.
                if hasattr(fr, '_forward_route_meta'):
                    r.add_forward_func(fr)
                else:
                    r.add_forward(*fr)

        if hasattr(plugin, reverse_route_attr):
            for rr in getattr(plugin, reverse_route_attr):
                # An annotated function can also be passed in directly.
                if hasattr(rr, '_reverse_route_src'):
                    r.add_reverse_func(rr)
                else:
                    r.add_reverse(*rr)

        if hasattr(plugin, view_attr):
            for v in getattr(plugin, view_attr):
                r.add_view(*v)

    return r

def handler(apachereq):
    """Handles an HTTP request.

    Intended to be called by mod_python, as a handler.

    @param apachereq: An Apache request object.
    """
    # Make the request object into an IVLE request which can be given to views
    req = Request(apachereq, config)

    # Hack? Try and get the user login early just in case we throw an error
    # (most likely 404) to stop us seeing not logged in even when we are.
    if not req.publicmode:
        user = ivle.webapp.security.get_user_details(req)

        # Don't set the user if it is disabled or hasn't accepted the ToS.
        if user and user.valid:
            req.user = user

    req.publisher = generate_publisher(
        config.plugin_index[ViewPlugin],
        ApplicationRoot(req.config, req.store, req.user),
        publicmode=req.publicmode)

    try:
        obj, viewcls, subpath = req.publisher.resolve(req.uri.decode('utf-8'))
        try:
            # We 404 if we have a subpath but the view forbids it.
            if not viewcls.subpath_allowed and subpath:
                raise NotFound()

            # Instantiate the view, which should be a BaseView class
            view = viewcls(req, obj, subpath)

            # Check that the request (mainly the user) is permitted to access
            # the view.
            if not view.authorize(req):
                # Indicate the forbidden object if this is an admin.
                if req.user and req.user.admin:
                    raise Unauthorized('Unauthorized: %s' % view)
                else:
                    raise Unauthorized()

            # Non-GET requests from other sites leave us vulnerable to
            # CSRFs. Block them.
            referer = req.headers_in.get('Referer')
            if (referer is None or
                urlparse.urlparse(req.headers_in.get('Referer')).netloc !=
                    req.hostname):
                if req.method != 'GET' and not view.offsite_posts_allowed:
                    raise BadRequest(
                        "Non-GET requests from external sites are forbidden "
                        "for security reasons.")

            # Render the output
            view.render(req)
        except HTTPError, e:
            # A view explicitly raised an HTTP error. Respect it.
            req.status = e.code

            # Try to find a custom error view.
            if hasattr(viewcls, 'get_error_view'):
                errviewcls = viewcls.get_error_view(e)
            else:
                errviewcls = XHTMLView.get_error_view(e)

            if errviewcls:
                errview = errviewcls(req, e, obj)
                errview.render(req)
                return req.OK
            elif e.message:
                req.write(e.message)
                return req.OK
            else:
                return e.code
        except mod_python.apache.SERVER_RETURN:
            # A mod_python-specific Apache error.
            # XXX: We need to raise these because req.throw_error() uses them.
            # Remove this after Google Code issue 117 is fixed.
            raise
        except Exception, e:
            # A non-HTTPError appeared. We have an unknown exception. Panic.
            handle_unknown_exception(req, *sys.exc_info())
            return req.OK
        else:
            req.store.commit()
            return req.OK
    except Unauthorized, e:
        # Resolution failed due to a permission check. Display a pretty
        # error, or maybe a login page.
        XHTMLView.get_error_view(e)(req, e, req.publisher.root).render(req)
        return req.OK
    except PublishingError, e:
        req.status = 404

        if req.user and req.user.admin:
            XHTMLErrorView(req, NotFound('Not found: ' +
                                         str(e.args)), e[0]).render(req)
        else:
            XHTMLErrorView(req, NotFound(), e[0]).render(req)

        return req.OK
    finally:
        req.store.close()

def handle_unknown_exception(req, exc_type, exc_value, exc_traceback):
    """
    Given an exception that has just been thrown from IVLE, print its details
    to the request.
    This is a full handler. It assumes nothing has been written, and writes a
    complete HTML page.
    req: May be EITHER an IVLE req or an Apache req.
    The handler code may pass an apache req if an exception occurs before
    the IVLE request is created.
    """
    req.content_type = "text/html"
    logfile = os.path.join(config['paths']['logs'], 'ivle_error.log')
    logfail = False

    # XXX: This remains here for ivle.interpret's IVLEErrors. Once we rewrite
    #      fileservice, req.status should always be 500 (ISE) here.
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

    # A "bad" error message. We shouldn't get here unless IVLE
    # misbehaves (which is currently very easy, if things aren't set up
    # correctly).
    # Write the traceback.

    # We need to special-case IVLEJailError, as we can get another
    # almost-exception out of it.
    if exc_type is util.IVLEJailError:
        tb = 'Exception information extracted from IVLEJailError:\n'
        tb += urllib.unquote(exc_value.info)
    else:
        tb = ''.join(traceback.format_exception(exc_type, exc_value,
                                                exc_traceback))

    logging.error('\n' + tb)

    # Error messages are only displayed is the user is NOT a student,
    # or if there has been a problem logging the error message
    show_errors = (not publicmode) and ((login and req.user.admin) or logfail)
    req.write("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"                 
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">                                      
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>IVLE Internal Server Error</title></head>
<body>
<h1>IVLE Internal Server Error</h1>
<p>An error has occured which is the fault of the IVLE developers or
administrators. """)

    if logfail:
        req.write("Please report this issue to the server administrators, "
                  "along with the following information.")
    else:
        req.write("Details have been logged for further examination.")
    req.write("</p>")

    if show_errors:
        req.write("<h2>Debugging information</h2>")
        req.write("<pre>\n%s\n</pre>\n"%cgi.escape(tb))
    req.write("</body></html>")
