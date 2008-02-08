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

# Module: cgirequest
# Author: Matt Giuca
# Date:   5/2/2007

# Presents a CGIRequest class which creates an object compatible with IVLE
# Request objects (the same interface exposed by www.dispatch.request) from a
# CGI script.
# This allows CGI scripts to create request objects and then pass them to
# normal IVLE handlers.

# NOTE: This object does not support write_html_head_foot (simply because we
# do not need it in its intended application: fileservice).

import sys
import os
import cgi

import conf
import common
import common.util

# Utility functions

def _http_headers_in_from_cgi():
    """Returns a dictionary of HTTP headers and their values, reading from the
    CGI environment."""
    d = {}
    for k in os.environ.keys():
        if k.startswith("HTTP_"):
            # Change the case - underscores become - and each word is
            # capitalised
            varname = '-'.join(map(lambda x: x[0:1] + x[1:].lower(),
                                k[5:].split('_')))
            d[varname] = os.environ[k]
    return d

class CGIRequest:
    """An IVLE request object, built from a CGI script. This is presented to
    the IVLE apps as a way of interacting with the CGI server.
    See dispatch.request for a full interface specification.
    """

    # COPIED from dispatch/request.py
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

    def __init__(self):
        """Builds an CGI Request object from the current CGI environment.
        This results in an object with all of the necessary methods and
        additional fields.
        """
        self.headers_written = False

        if ('SERVER_NAME' not in os.environ or
            'REQUEST_METHOD' not in os.environ or
            'REQUEST_URI' not in os.environ):
            raise Exception("No CGI environment found")

        # Determine if the browser used the public host name to make the
        # request (in which case we are in "public mode")
        if os.environ['SERVER_NAME'] == conf.public_host:
            self.publicmode = True
        else:
            self.publicmode = False

        # Inherit values for the input members
        self.method = os.environ['REQUEST_METHOD']
        self.uri = os.environ['REQUEST_URI']
        # Split the given path into the app (top-level dir) and sub-path
        # (after first stripping away the root directory)
        path = common.util.unmake_path(self.uri)
        if self.publicmode:
            self.app = None
            self.path = path
        else:
            (self.app, self.path) = (common.util.split_path(path))
        self.username = None
        self.hostname = os.environ['SERVER_NAME']
        self.headers_in = _http_headers_in_from_cgi()
        self.headers_out = {}

        # Default values for the output members
        self.status = CGIRequest.HTTP_OK
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
        if 'Content-Type' in self.headers_out:
            self.content_type = self.headers_out['Content-Type']
        if 'Location' in self.headers_out:
            self.location = self.headers_out['Location']

        # CGI allows for four response types: Document, Local Redirect, Client
        # Redirect, and Client Redirect w/ Document
        # XXX We do not allow Local Redirect
        if self.location != None:
            # This is a Client Redirect
            print "Location: %s" % self.location
            if self.content_type == None:
                # Just redirect
                return
            # Else: This is a Client Redirect with Document
            print "Status: %d" % self.status
            print "Content-Type: %s" % self.content_type
        else:
            # This is a Document response
            print "Content-Type: %s" % self.content_type
            print "Status: %d" % self.status

        # Print the other headers
        for k,v in self.headers_out.items():
            if k != 'Content-Type' and k != 'Location':
                print "%s: %s" % (k, v)

        # XXX write_html_head_foot not supported
        #if self.write_html_head_foot:
        #    # Write the HTML header, pass "self" (request object)
        #    self.func_write_html_head(self)
        # Print a blank line to signal the start of output
        print

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
            sys.stdout.write(string.encode('utf8'))
        else:
            # 8-bit clean strings just get written directly.
            # This includes binary strings.
            sys.stdout.write(string)

    def flush(self):
        """Flushes the output buffer."""
        sys.stdout.flush()

    def sendfile(self, filename):
        """Sends the named file directly to the client."""
        if not self.headers_written:
            self.__writeheaders()
        f = open(filename)
        buf = f.read(1024)
        while len(buf) > 0:
            sys.stdout.write(buf)
            sys.stdout.flush()
            buf = f.read(1024)
        f.close()

    def read(self, len=None):
        """Reads at most len bytes directly from the client. (See mod_python
        Request.read)."""
        if len is None:
            return sys.stdin.read()
        else:
            return sys.stdin.read(len)

    def throw_error(self, httpcode):
        """Writes out an HTTP error of the specified code. Exits the process,
        so any code following this call will not be executed.

        (This is justified because of the nature of CGI, it is a single-script
        environment, there is no containing process which needs to catch an
        exception).

        httpcode: An HTTP response status code. Pass a constant from the
        Request class.
        """
        self.status = httpcode
        self.content_type = "text/html"
        # Emulate an Apache error
        self.write("""<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>%d Error</title>
</head><body>
<h1>Error</h1>
<p>A %d error was triggered by a CGI app.</p>
</body></html>
""" % (httpcode, httpcode))
        # Exit the process completely
        self.flush()
        sys.exit(httpcode)

    def throw_redirect(self, location):
        """Writes out an HTTP redirect to the specified URL. Exits the
        process, so any code following this call will not be executed.

        httpcode: An HTTP response status code. Pass a constant from the
        Request class.
        """
        self.status = CGIRequest.HTTP_MOVED_TEMPORARILY
        self.location = location
        self.ensure_headers_written()
        self.flush()
        sys.exit(self.status)

    def get_session(self):
        """Returns a mod_python Session object for this request.
        Note that this is dependent on mod_python and may need to change
        interface if porting away from mod_python."""
        # Cache the session object
        if not hasattr(self, 'session'):
            #self.session = Session.FileSession(self.apache_req)
            self.session = None
            # FIXME: How to get session?
        return self.session

    def get_fieldstorage(self):
        """Returns a mod_python FieldStorage object for this request.
        Note that this is dependent on mod_python and may need to change
        interface if porting away from mod_python."""
        # Cache the fieldstorage object
        if not hasattr(self, 'fields'):
            self.fields = cgi.FieldStorage()
        return self.fields

    def get_cgi_environ(self):
        """Returns the CGI environment emulation for this request. (Calls
        add_common_vars). The environment is returned as a mapping
        compatible with os.environ."""
        return os.environ
