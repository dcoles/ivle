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

# Author: Matt Giuca

"""
IVLE Request Object

Builds an IVLE request object from a mod_python request object.
See design notes/apps/dispatch.txt for a full specification of this request
object.
"""

try:
    import mod_python.Session
    import mod_python.Cookie
    import mod_python.util
    import mod_python.apache

    class PotentiallySecureFileSession(mod_python.Session.FileSession):
        """A mod_python FileSession that sets secure cookie when appropriate.

        A secure cookie will be set if the request itself is over HTTPS, or if
        a proxy in front has set X-Forwarded-Proto: https. Otherwise the cookie
        will be insecure.
        """
        def make_cookie(self):
            cookie = super(PotentiallySecureFileSession, self).make_cookie()
            if (self._req.is_https() or
                self._req.headers_in.get('X-Forwarded-Proto') == 'https'):
                cookie.secure = True
            return cookie
except ImportError:
    # This needs to be importable from outside Apache.
    pass

import os.path

import ivle.util
import ivle.database
from ivle.webapp.base.plugins import CookiePlugin
import ivle.webapp.security


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
        store (read)
            storm.store.Store instance. Holds a database transaction open,
            which is available for the entire lifetime of the request.
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
        content_length (write)
            Integer. The number of octets to be transfered.
        location (write)
            String. Response "Location" header value. Used with HTTP redirect
            responses.
    """

    # Special code for an OK response.
    # Do not use HTTP_OK; for some reason Apache produces an "OK" error
    # message if you do that.
    OK  = 0

    # HTTP status codes

    HTTP_OK                           = 200
    HTTP_MOVED_TEMPORARILY            = 302
    HTTP_FORBIDDEN                    = 403
    HTTP_NOT_FOUND                    = 404
    HTTP_INTERNAL_SERVER_ERROR        = 500

    _store = None

    def __init__(self, req, config):
        """Create an IVLE request from a mod_python one.

        @param req: A mod_python request.
        @param config: An IVLE configuration.
        """

        # Methods are mostly wrappers around the Apache request object
        self.apache_req = req
        self.config = config
        self.headers_written = False

        # Determine if the browser used the public host name to make the
        # request (in which case we are in "public mode")
        if req.hostname == config['urls']['public_host']:
            self.publicmode = True
        else:
            self.publicmode = False

        # Inherit values for the input members
        self.method = req.method
        self.uri = req.uri
        # Split the given path into the app (top-level dir) and sub-path
        # (after first stripping away the root directory)
        (self.app, self.path) = (ivle.util.split_path(req.uri))
        self.hostname = req.hostname
        self.headers_in = req.headers_in
        self.headers_out = req.headers_out

        # Default values for the output members
        self.status = Request.HTTP_OK
        self.content_type = None        # Use Apache's default
        self.content_length = None        # Don't provide Content-Length
        self.location = None
        # In some cases we don't want the template JS (such as the username
        # and public FQDN) in the output HTML. In that case, set this to 0.
        self.write_javascript_settings = True
        self.got_common_vars = False

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        """Cleanup."""
        if self._store is not None:
            self._store.close()
            self._store = None

    def commit(self):
        """Cleanup."""
        if self._store is not None:
            self._store.commit()

    def __writeheaders(self):
        """Writes out the HTTP and HTML headers before any real data is
        written."""
        self.headers_written = True

        # Prepare the HTTP and HTML headers before the first write is made
        if self.content_type != None:
            self.apache_req.content_type = self.content_type
        if self.content_length:
            self.apache_req.set_content_length(self.content_length)
        self.apache_req.status = self.status
        if self.location != None:
            self.apache_req.headers_out['Location'] = self.location

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

    def logout(self):
        """Log out the current user by destroying the session state.
        Then redirect to the top-level IVLE page."""
        if hasattr(self, 'session'):
            self.session.invalidate()
            self.session.delete()
            # Invalidates all IVLE cookies
            all_cookies = mod_python.Cookie.get_cookies(self)

            # Create cookies for plugins that might request them.
            for plugin in self.config.plugin_index[CookiePlugin]:
                for cookie in plugin.cookies:
                    self.add_cookie(mod_python.Cookie.Cookie(cookie, '',
                                                    expires=1, path='/'))
        self.throw_redirect(self.make_path(''))


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

    def throw_redirect(self, location):
        """Writes out an HTTP redirect to the specified URL. Raises an
        exception which is caught by the dispatch or web server, so any
        code following this call will not be executed.

        httpcode: An HTTP response status code. Pass a constant from the
        Request class.
        """
        # Note: location may be a unicode, but it MUST only have ASCII
        # characters (non-ascii characters should be URL-encoded).
        mod_python.util.redirect(self.apache_req, location.encode("ascii"))

    def add_cookie(self, cookie, value=None, **attributes):
        """Inserts a cookie into this request object's headers."""
        if value is None:
            mod_python.Cookie.add_cookie(self.apache_req, cookie)
        else:
            mod_python.Cookie.add_cookie(self.apache_req, cookie, value, **attributes)

    def make_path(self, path):
        """Prepend the IVLE URL prefix to the given path.

        This is used when generating URLs to send to the client.

        This method is DEPRECATED. We no longer support use of a prefix.
        """
        return os.path.join(self.config['urls']['root'], path)

    def get_session(self):
        """Returns a mod_python Session object for this request.
        Note that this is dependent on mod_python and may need to change
        interface if porting away from mod_python.

        IMPORTANT: Call unlock() on the session as soon as you are done with
                   it! If you don't, all other requests will block!
        """
        # Cache the session object and set the timeout to 24 hours.
        if not hasattr(self, 'session'):
            self.session = PotentiallySecureFileSession(
                self.apache_req, timeout = 60 * 60 * 24)
        return self.session

    def get_fieldstorage(self):
        """Returns a mod_python FieldStorage object for this request.
        Note that this is dependent on mod_python and may need to change
        interface if porting away from mod_python."""
        # Cache the fieldstorage object
        if not hasattr(self, 'fields'):
            self.fields = mod_python.util.FieldStorage(self.apache_req)
        return self.fields

    def get_cgi_environ(self):
        """Returns the CGI environment emulation for this request. (Calls
        add_common_vars). The environment is returned as a mapping
        compatible with os.environ."""
        if not self.got_common_vars:
            self.apache_req.add_common_vars()
            self.got_common_vars = True
        return self.apache_req.subprocess_env

    @property
    def store(self):
        # Open a database connection and transaction, keep it around for users
        # of the Request object to use.
        if self._store is None:
            self._store = ivle.database.get_store(self.config)
        return self._store

    @property
    def user(self):
        # Get and cache the request user, or None if it's not valid.
        # This is a property so that we don't create a store unless
        # some code actually requests the user.
        try:
            return self._user
        except AttributeError:
            if self.publicmode:
                self._user = None
            else:
                temp_user = ivle.webapp.security.get_user_details(self)
                if temp_user and temp_user.valid:
                    self._user = temp_user
                else:
                    self._user = None
            return self._user

