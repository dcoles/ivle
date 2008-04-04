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

# Module: dispatch.request
# Author: Matt Giuca
# Date:   12/12/2007

# Builds an IVLE request object from a mod_python request object.
# See design notes/apps/dispatch.txt for a full specification of this request
# object.

import common.util
import mod_python
from mod_python import (util, Session, Cookie)
import conf

class Request:
    """An IVLE request object. This is presented to the IVLE apps as a way of
    interacting with the web server and the dispatcher.

    Request object attributes:
        method (read)
            String. The request method (eg. 'GET', 'POST', etc)
        uri (read)
            String. The path portion of the URI.
        app (read)
            String. Name of the application specified in the URL, or None.
        path (read)
            String. The path specified in the URL *not including* the
            application or the IVLE location prefix. eg. a URL of
            "/ivle/files/joe/myfiles" has a path of "joe/myfiles".
        user (read)
            User object. Details of the user who is currently logged in, or
            None.
        hostname (read)
            String. Hostname the server is running on.
        headers_in (read)
            Table object representing headers sent by the client.
        headers_out (read, can be written to)
            Table object representing headers to be sent to the client.
        publicmode (read)
            Bool. True if the request came for the "public host" as
            configured in conf.py. Note that public mode requests do not
            have an app (app is set to None).

        status (write)
            Int. Response status number. Use one of the status codes defined
            in class Request.
        content_type (write)
            String. The Content-Type (mime type) header value.
        location (write)
            String. Response "Location" header value. Used with HTTP redirect
            responses.
        title (write)
            String. HTML page title. Used if write_html_head_foot is True, in
            the HTML title element text.
        styles (write)
            List of strings. Write a list of URLs to CSS files here, and they
            will be incorporated as <link rel="stylesheet" type="text/css">
            elements in the head, if write_html_head_foot is True.
            URLs should be relative to the IVLE root; they will be fixed up
            to be site-relative.
        scripts (write)
            List of strings. Write a list of URLs to JS files here, and they
            will be incorporated as <script type="text/javascript"> elements
            in the head, if write_html_head_foot is True.
            URLs should be relative to the IVLE root; they will be fixed up
            to be site-relative.
        write_html_head_foot (write)
            Boolean. If True, dispatch assumes that this is an XHTML page, and
            will immediately write a full HTML head, open the body element,
            and write heading contents to the page, before any bytes are
            written. It will then write footer contents and close the body and
            html elements at the end of execution.  

            This value should be set to true by all applications for all HTML
            output (unless there is a good reason, eg. exec). The
            applications should therefore output HTML content assuming that
            it will be written inside the body tag. Do not write opening or
            closing <html> or <body> tags.
    """

    # Special code for an OK response.
    # Do not use HTTP_OK; for some reason Apache produces an "OK" error
    # message if you do that.
    OK  = 0

    # HTTP status codes

    HTTP_CONTINUE                     = 100
    HTTP_SWITCHING_PROTOCOLS          = 101
    HTTP_PROCESSING                   = 102
    HTTP_OK                           = 200
    HTTP_CREATED                      = 201
    HTTP_ACCEPTED                     = 202
    HTTP_NON_AUTHORITATIVE            = 203
    HTTP_NO_CONTENT                   = 204
    HTTP_RESET_CONTENT                = 205
    HTTP_PARTIAL_CONTENT              = 206
    HTTP_MULTI_STATUS                 = 207
    HTTP_MULTIPLE_CHOICES             = 300
    HTTP_MOVED_PERMANENTLY            = 301
    HTTP_MOVED_TEMPORARILY            = 302
    HTTP_SEE_OTHER                    = 303
    HTTP_NOT_MODIFIED                 = 304
    HTTP_USE_PROXY                    = 305
    HTTP_TEMPORARY_REDIRECT           = 307
    HTTP_BAD_REQUEST                  = 400
    HTTP_UNAUTHORIZED                 = 401
    HTTP_PAYMENT_REQUIRED             = 402
    HTTP_FORBIDDEN                    = 403
    HTTP_NOT_FOUND                    = 404
    HTTP_METHOD_NOT_ALLOWED           = 405
    HTTP_NOT_ACCEPTABLE               = 406
    HTTP_PROXY_AUTHENTICATION_REQUIRED= 407
    HTTP_REQUEST_TIME_OUT             = 408
    HTTP_CONFLICT                     = 409
    HTTP_GONE                         = 410
    HTTP_LENGTH_REQUIRED              = 411
    HTTP_PRECONDITION_FAILED          = 412
    HTTP_REQUEST_ENTITY_TOO_LARGE     = 413
    HTTP_REQUEST_URI_TOO_LARGE        = 414
    HTTP_UNSUPPORTED_MEDIA_TYPE       = 415
    HTTP_RANGE_NOT_SATISFIABLE        = 416
    HTTP_EXPECTATION_FAILED           = 417
    HTTP_UNPROCESSABLE_ENTITY         = 422
    HTTP_LOCKED                       = 423
    HTTP_FAILED_DEPENDENCY            = 424
    HTTP_INTERNAL_SERVER_ERROR        = 500
    HTTP_NOT_IMPLEMENTED              = 501
    HTTP_BAD_GATEWAY                  = 502
    HTTP_SERVICE_UNAVAILABLE          = 503
    HTTP_GATEWAY_TIME_OUT             = 504
    HTTP_VERSION_NOT_SUPPORTED        = 505
    HTTP_VARIANT_ALSO_VARIES          = 506
    HTTP_INSUFFICIENT_STORAGE         = 507
    HTTP_NOT_EXTENDED                 = 510

    def __init__(self, req, write_html_head):
        """Builds an IVLE request object from a mod_python request object.
        This results in an object with all of the necessary methods and
        additional fields.

        req: A mod_python request object.
        write_html_head: Function which is called when writing the automatic
            HTML header. Accepts a single argument, the IVLE request object.
        """

        # Methods are mostly wrappers around the Apache request object
        self.apache_req = req
        self.func_write_html_head = write_html_head
        self.headers_written = False

        # Determine if the browser used the public host name to make the
        # request (in which case we are in "public mode")
        if req.hostname == conf.public_host:
            self.publicmode = True
        else:
            self.publicmode = False

        # Inherit values for the input members
        self.method = req.method
        self.uri = req.uri
        # Split the given path into the app (top-level dir) and sub-path
        # (after first stripping away the root directory)
        path = common.util.unmake_path(req.uri)
        if self.publicmode:
            self.app = None
            (_, self.path) = (common.util.split_path(path))
        else:
            (self.app, self.path) = (common.util.split_path(path))
        self.user = None
        self.hostname = req.hostname
        self.headers_in = req.headers_in
        self.headers_out = req.headers_out

        # Default values for the output members
        self.status = Request.HTTP_OK
        self.content_type = None        # Use Apache's default
        self.location = None
        self.title = None     # Will be set by dispatch before passing to app
        self.styles = []
        self.scripts = []
        self.write_html_head_foot = False
        self.got_common_vars = False

    def __writeheaders(self):
        """Writes out the HTTP and HTML headers before any real data is
        written."""
        self.headers_written = True
        # Prepare the HTTP and HTML headers before the first write is made
        if self.content_type != None:
            self.apache_req.content_type = self.content_type
        self.apache_req.status = self.status
        if self.location != None:
            self.apache_req.headers_out['Location'] = self.location
        if self.write_html_head_foot:
            # Write the HTML header, pass "self" (request object)
            self.func_write_html_head(self)

    def ensure_headers_written(self):
        """Writes out the HTTP and HTML headers if they haven't already been
        written."""
        if not self.headers_written:
            self.__writeheaders()

    def write(self, string, flush=1):
        """Writes string directly to the client, then flushes the buffer,
        unless flush is 0."""

        if not self.headers_written:
            self.__writeheaders()
        if isinstance(string, unicode):
            # Encode unicode strings as UTF-8
            # (Otherwise cannot handle being written to a bytestream)
            self.apache_req.write(string.encode('utf8'), flush)
        else:
            # 8-bit clean strings just get written directly.
            # This includes binary strings.
            self.apache_req.write(string, flush)

    def flush(self):
        """Flushes the output buffer."""
        self.apache_req.flush()

    def sendfile(self, filename):
        """Sends the named file directly to the client."""
        if not self.headers_written:
            self.__writeheaders()
        self.apache_req.sendfile(filename)

    def read(self, len=None):
        """Reads at most len bytes directly from the client. (See mod_python
        Request.read)."""
        if len is None:
            return self.apache_req.read()
        else:
            return self.apache_req.read(len)

    def throw_error(self, httpcode, message=None):
        """Writes out an HTTP error of the specified code. Raises an exception
        which is caught by the dispatch or web server, so any code following
        this call will not be executed.

        httpcode: An HTTP response status code. Pass a constant from the
        Request class.
        """
        raise common.util.IVLEError(httpcode, message)

    def throw_redirect(self, location):
        """Writes out an HTTP redirect to the specified URL. Raises an
        exception which is caught by the dispatch or web server, so any
        code following this call will not be executed.

        httpcode: An HTTP response status code. Pass a constant from the
        Request class.
        """
        mod_python.util.redirect(self.apache_req, location)

    def add_cookie(self, cookie, value=None, **attributes):
        """Inserts a cookie into this request object's headers."""
        if value is None:
            Cookie.add_cookie(self.apache_req, cookie)
        else:
            Cookie.add_cookie(self.apache_req, cookie, value, **attributes)

    def get_session(self):
        """Returns a mod_python Session object for this request.
        Note that this is dependent on mod_python and may need to change
        interface if porting away from mod_python."""
        # Cache the session object and set the timeout to 24 hours.
        if not hasattr(self, 'session'):
            self.session = Session.FileSession(self.apache_req,
                                               timeout = 60 * 60 * 24)
        return self.session

    def get_fieldstorage(self):
        """Returns a mod_python FieldStorage object for this request.
        Note that this is dependent on mod_python and may need to change
        interface if porting away from mod_python."""
        # Cache the fieldstorage object
        if not hasattr(self, 'fields'):
            self.fields = util.FieldStorage(self.apache_req)
        return self.fields

    def get_cgi_environ(self):
        """Returns the CGI environment emulation for this request. (Calls
        add_common_vars). The environment is returned as a mapping
        compatible with os.environ."""
        if not self.got_common_vars:
            self.apache_req.add_common_vars()
            self.got_common_vars = True
        return self.apache_req.subprocess_env

    @staticmethod
    def get_http_codename(code):
        """Given a HTTP error code int, returns a (name, description)
        pair, suitable for displaying to the user.
        May return (None,None) if code is unknown.
        Only lists common 4xx and 5xx codes (since this is just used
        to display throw_error error messages).
        """
        try:
            return http_codenames[code]
        except KeyError:
            return None, None

# Human strings for HTTP response codes
http_codenames = {
    Request.HTTP_BAD_REQUEST:
        ("Bad Request",
        "Your browser sent a request IVLE did not understand."),
    Request.HTTP_UNAUTHORIZED:
        ("Unauthorized",
        "You are not allowed to view this part of IVLE."),
    Request.HTTP_FORBIDDEN:
        ("Forbidden",
        "You are not allowed to view this part of IVLE."),
    Request.HTTP_NOT_FOUND:
        ("Not Found",
        "The application or file you requested does not exist."),
    Request.HTTP_METHOD_NOT_ALLOWED:
        ("Method Not Allowed",
        "Your browser is interacting with IVLE in the wrong way."
        "This is probably a bug in IVLE. "
        "Please report it to the administrators."),
    Request.HTTP_INTERNAL_SERVER_ERROR:
        ("Internal Server Error",
        "An unknown error occured in IVLE."),
    Request.HTTP_NOT_IMPLEMENTED:
        ("Not Implemented",
        "The application or file you requested has not been implemented "
        "in IVLE."),
    Request.HTTP_SERVICE_UNAVAILABLE:
        ("Service Unavailable",
        "IVLE is currently experiencing technical difficulties. "
        "Please try again later."),
}
