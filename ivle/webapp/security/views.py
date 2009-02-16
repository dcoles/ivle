# IVLE
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

# Author: Will Grant, Nick Chadwick

import urllib
import datetime
try:
    import mod_python.Cookie
except ImportError:
    # This needs to be importable from outside Apache.
    pass

import ivle.util
from ivle.auth import authenticate, AuthError
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import CookiePlugin
from ivle.dispatch.login import get_user_details

class LoginView(XHTMLView):
    '''A view to allow a user to log in.'''
    template = 'login.html'

    def authorize(self, req):
        return True

    def populate(self, req, ctx):
        fields = req.get_fieldstorage()
        nexturl = fields.getfirst('url')

        if nexturl is None:
            nexturl = '/'

        # We are already logged in. Don't bother logging in again.
        if req.user is not None:
            req.throw_redirect(nexturl)

        ctx['path'] = ivle.util.make_path('+login') + \
                         '?' + urllib.urlencode([('url', nexturl)])

        if req.method == "POST":
            # While req.user is normally set to get_user_details, it won't set
            # it if the account isn't valid. So we get it ourselves.
            user = get_user_details(req)

            badlogin = None

            username = fields.getfirst('user')
            password = fields.getfirst('pass')
            if username is not None:
                # From this point onwards, we will be showing an error message
                # if unsuccessful.
                # Authenticate
                if password is None:
                    badlogin = "No password supplied."
                else:
                    user = None
                    try:
                        user = authenticate.authenticate(req.store,
                                    username.value, password.value)
                    except AuthError, msg:
                        badlogin = msg
                    if user is None:
                        # Must have got an error. Do not authenticate.
                        # The except: above will have set a message.
                        pass
                    else:
                        # Success - Set the session and redirect to the URL.
                        session = req.get_session()
                        session['login'] = user.login
                        session.save()
                        user.last_login = datetime.datetime.now()
                        req.store.commit()

                        # Create cookies for plugins that might request them.
                        for plugin in req.plugin_index[CookiePlugin]:
                            for cookie in plugin.cookies:
                                # The function can be None if they just need to be
                                # deleted at logout.
                                if plugin.cookies[cookie] is not None:
                                    req.add_cookie(mod_python.Cookie.Cookie(cookie,
                                          plugin.cookies[cookie](user), path='/'))

                        req.throw_redirect(nexturl)

                # We didn't succeed.
                # Render the login form with the error message.
                ctx['error'] = badlogin


class LogoutView(XHTMLView):
    '''A view to log the current session out.'''
    template = 'logout.html'

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        if req.method == "POST":
            req.logout()
        else:
            ctx['path'] =  ivle.util.make_path('+logout')
