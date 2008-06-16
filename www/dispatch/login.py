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

# Module: dispatch.login
# Author: Matt Giuca
# Date: 21/12/2007

# Provides services for checking logins and presenting the login page.
import os
import time

from mod_python import Session

import conf
from common import (util, db, caps, forumutil)
from auth import authenticate, autherror

def login(req):
    """Determines whether the user is logged in or not (looking at sessions),
    and if not, presents the login page. Returns a User object, or None
    if not logged in.

    If the user was already logged in, nothing is written to req. Returns
    the User object for the logged in user.

    If the user was not logged in, but manages to authenticate due to
    included postdata with a valid username/password, throws a redirect
    back to the same page (to avoid leaving POSTDATA in the browser).

    If the user is not logged in, or fails to authenticate, a full page is
    written to req. Returns None. The caller should immediately terminate.
    """
    # Get the user details from the session, if already logged in
    # (None means not logged in yet)
    login_details = get_user_details(req)

    # Check the session to see if someone is logged in. If so, go with it.
    # No security is required here. You must have already been authenticated
    # in order to get a 'login_name' variable in the session.
    if login_details is not None and login_details.state == "enabled":
        # Only allow users to authenticate if their account is ENABLED
        return login_details

    badlogin = None

    # Check if there is any postdata containing login information
    if login_details is None and req.method == 'POST':
        fields = req.get_fieldstorage()
        username = fields.getfirst('user')
        password = fields.getfirst('pass')
        if username is not None:
            # From this point onwards, we will be showing an error message
            # if unsuccessful.
            # Authenticate
            if password is None:
                badlogin = "No password supplied."
            else:
                try:
                    login_details = \
                        authenticate.authenticate(username.value, password.value)
                # NOTE: Can't catch AuthError, since each module throws a
                # different identity of AuthError.
                except Exception, msg:
                    badlogin = msg
                if login_details is None:
                    # Must have got an error. Do not authenticate.
                    pass
                elif login_details.pass_expired():
                    badlogin = "Your password has expired."
                elif login_details.acct_expired():
                    badlogin = "Your account has expired."
                else:
                    # Success - Set the session and redirect to avoid POSTDATA
                    session = req.get_session()
                    session['user'] = login_details
                    session.save()
                    db.DB().update_user(username.value,
                                        last_login = time.localtime())
                    req.add_cookie(forumutil.make_forum_cookie(login_details))
                    req.throw_redirect(req.uri)

    # Present the HTML login page
    req.content_type = "text/html"
    req.title = "Login"
    req.write_html_head_foot = True

    # User is not logged in or their account is not enabled.
    if login_details is not None:
        # Only possible if no errors occured thus far
        if login_details.state == "no_agreement":
            # User has authenticated but has not accepted the TOS.
            # Present them with the TOS page.
            # First set their username for display at the top, but make sure
            # the apps tabs are not displayed
            req.user = login_details
            # IMPORTANT NOTE FOR HACKERS: You can't simply disable this check
            # if you are not planning to display a TOS page - the TOS
            # acceptance process actually calls usermgt to create the user
            # jails and related stuff.
            present_tos(req, login_details.fullname)
            return None
        elif login_details.state == "disabled":
            # User has authenticated but their account is disabled
            badlogin = "Your account has been disabled."
        elif login_details.state == "pending":
            # FIXME: this isn't quite the right answer, but it
            # should be more robust in the short term.
            session = req.get_session()
            session.invalidate()
            session.delete()
            db.DB().update_user(login_details.login, state='no_agreement')
            req.throw_redirect(req.uri)

    # Write the HTML for the login page
    # If badlogin, display an error message indicating a failed login
    req.write("""<div id="ivle_padding">
<p>Welcome to the Informatics Virtual Learning Environment.
   Please log in to access your files and assessment.</p>
""")
    if badlogin is not None:
        req.write("""<p class="error">%s</p>
""" % badlogin)
    req.write("""<form action="" method="post">
  <table>
    <tr><td>Username:</td><td><input name="user" type="text" /></td></tr>
    <tr><td>Password:</td><td><input name="pass" type="password" /></td></tr>
    <tr><td colspan="2"><input type="submit" value="Login" /></td></tr>
  </table>
</form>
""")
    # Write the "Message of the Day" document, if it exists.
    try:
        req.sendfile(conf.motd_path)
    except IOError:
        pass
    req.write('</div>\n')

    return None

def get_user_details(req):
    """Gets the name of the logged in user, without presenting a login box
    or attempting to authenticate.
    Returns None if there is no user logged in.
    """
    session = req.get_session()

    # Check the session to see if someone is logged in. If so, go with it.
    # No security is required here. You must have already been authenticated
    # in order to get a 'login_name' variable in the session.
    try:
        return session['user']
    except KeyError:
        return None

def present_tos(req, fullname):
    """Present the Terms of Service screen to the user (who has just logged in
    for the first time and needs to accept these before being admitted into
    the system).
    """
    req.title = "Terms of Service"
    # Include the JavaScript for the "makeuser" Ajax stuff
    req.scripts = [
        "media/common/json2.js",
        "media/common/util.js",
        "media/common/tos.js",
    ]
    req.write("""<div id="ivle_padding">
<p>Welcome, <b>%s</b>.</p>
<p>As this is the first time you have logged into IVLE, you are required to
accept these Terms of Service before using the system.</p>
<p>You will be allowed to re-read these terms at any time from the "Help"
menu.</p>
<hr />
""" % fullname)
    # Write out the text of the license
    util.send_terms_of_service(req)
    req.write("""<hr />
<div id="tos_acceptbuttons">
<p>Please click "I Accept" to indicate that you have read and understand these
terms, or click "I Decline" to log out of IVLE.</p>
<p>
  <input type="button" value="I Accept" onclick="accept_license()" />
  <input type="button" value="I Decline" onclick="decline_license()" />
</p>
</div>
""")

