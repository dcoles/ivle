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

import ivle.pulldown_subj
import ivle.webapp.security
from ivle.auth import authenticate, AuthError
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import CookiePlugin

class LoginView(XHTMLView):
    '''A view to allow a user to log in.'''
    template = 'login.html'
    allow_overlays = False

    def authorize(self, req):
        return True

    def populate(self, req, ctx):
        fields = req.get_fieldstorage()
        nexturl = fields.getfirst('url')

        if nexturl is None:
            nexturl = '/'

        # We are already logged in. If it is a POST, they might be trying to
        # clobber their session with some new credentials. That's their own
        # business, so we let them do it. Otherwise, we don't bother prompting
        # and just redirect to the destination.
        # Note that req.user is None even if we are 'logged in', if the user is
        # invalid (state != enabled, or expired).
        if req.method != "POST" and req.user is not None:
            req.throw_redirect(nexturl)

        # Don't give any URL if we want /.
        if nexturl == '/':
            query_string = ''
        else:
            query_string = '?url=' + urllib.quote(nexturl, safe="/~")

        ctx['path'] = req.make_path('+login') + query_string

        # If this succeeds, the user is invalid.
        user = ivle.webapp.security.get_user_details(req)
        if user is not None:
            if user.state == "no_agreement":
                # Authenticated, but need to accept the ToS. Send them there.
                # IMPORTANT NOTE FOR HACKERS: You can't simply disable this
                # if you are not planning to display a ToS page - the ToS
                # acceptance process actually calls usrmgt to create the user
                # jails and related stuff.
                req.throw_redirect(req.make_path('+tos') + query_string)
            elif user.state == "pending":
                # FIXME: this isn't quite the right answer, but it
                # should be more robust in the short term.
                session = req.get_session()
                session.invalidate()
                session.delete()
                user.state = u'no_agreement'
                req.store.commit()
                req.throw_redirect(nexturl)

        if req.method == "POST":
            # While req.user is normally set to get_user_details, it won't set
            # it if the account isn't valid. So we get it ourselves.
            user = ivle.webapp.security.get_user_details(req)

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
                        user = authenticate.authenticate(req.config, req.store,
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
                        session.unlock()
                        user.last_login = datetime.datetime.now()

                        # Create cookies for plugins that might request them.
                        for plugin in req.config.plugin_index[CookiePlugin]:
                            for cookie in plugin.cookies:
                                # The function can be None if they just need to be
                                # deleted at logout.
                                if plugin.cookies[cookie] is not None:
                                    req.add_cookie(mod_python.Cookie.Cookie(cookie,
                                          plugin.cookies[cookie](user), path='/'))

                        # Add any new enrolments.
                        ivle.pulldown_subj.enrol_user(req.config, req.store, user)
                        req.store.commit()

                        req.throw_redirect(nexturl)

                # We didn't succeed.
                # Render the login form with the error message.
                ctx['error'] = badlogin


class LogoutView(XHTMLView):
    '''A view to log the current session out.'''
    template = 'logout.html'
    allow_overlays = False

    def authorize(self, req):
        # This can be used by any authenticated user, even if they haven't
        # accepted the ToS yet.
        return ivle.webapp.security.get_user_details(req) is not None

    def populate(self, req, ctx):
        if req.method == "POST":
            req.logout()
        else:
            ctx['path'] =  req.make_path('+logout')
