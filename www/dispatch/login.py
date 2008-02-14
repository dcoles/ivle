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

from mod_python import Session

from common import util
from auth import authenticate

def login(req):
    """Determines whether the user is logged in or not (looking at sessions),
    and if not, presents the login page. Returns a String username, or None
    if not logged in.

    If the user was already logged in, nothing is written to req. Returns
    a string of the username.

    If the user was not logged in, but manages to authenticate due to
    included postdata with a valid username/password, throws a redirect
    back to the same page (to avoid leaving POSTDATA in the browser).

    If the user is not logged in, or fails to authenticate, a full page is
    written to req. Returns None. The caller should immediately terminate.
    """
    session = req.get_session()

    # Check the session to see if someone is logged in. If so, go with it.
    # No security is required here. You must have already been authenticated
    # in order to get a 'login_name' variable in the session.
    try:
        if session['state'] == "enabled":
            # Only allow users to authenticate if their account is ENABLED
            return session['login_name']
    except KeyError:
        pass

    badlogin = None
    # Check if there is any postdata containing login information
    if req.method == 'POST':
        fields = req.get_fieldstorage()
        username = fields.getfirst('user')
        password = fields.getfirst('pass')
        if username is not None:
            # From this point onwards, we will be showing an error message
            # if unsuccessful.
            # Authenticate
            if password is None:
                badlogin = "Invalid username or password."
            else:
                login_details = \
                    authenticate.authenticate(username.value, password.value)
                if login_details is None:
                    badlogin = "Invalid username or password."
                else:
                    # Success - Set the session and redirect to avoid POSTDATA
                    session['login_name'] = username.value
                    session['unixid'] = login_details['unixid']
                    session['state'] = login_details['state']
                    session['nick'] = login_details['nick']
                    session['fullname'] = login_details['fullname']
                    session['rolenm'] = login_details['rolenm']
                    session['studentid'] = login_details['studentid']
                    session.save()
                    req.throw_redirect(req.uri)

    # Give a 403 Forbidden status, but present a full HTML login page
    # instead of the usual 403 error.
    req.status = req.HTTP_FORBIDDEN
    req.content_type = "text/html"
    req.title = "Login"
    req.write_html_head_foot = True

    # User is not logged in or their account is not enabled.
    if 'state' in session:
        if session['state'] == "no_agreement":
            # User has authenticated but has not accepted the TOS.
            # Present them with the TOS page.
            # First set their username for display at the top, but make sure
            # the apps tabs are not displayed
            req.username = session['login_name']
            req.no_agreement = True
            # IMPORTANT NOTE FOR HACKERS: You can't simply disable this check
            # if you are not planning to display a TOS page - the TOS
            # acceptance process actually calls usermgt to create the user
            # jails and related stuff.
            present_tos(req, session['fullname'])
            return None
        elif session['state'] == "disabled":
            # User has authenticated but their account is disabled
            badlogin = "Can't log in: Your account has been disabled."
    # Else, just fall through (failed to authenticate)

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
</div>
""")

    return None

def get_username(req):
    """Gets the name of the logged in user, without presenting a login box
    or attempting to authenticate.
    Returns None if there is no user logged in.
    """
    session = req.get_session()

    # Check the session to see if someone is logged in. If so, go with it.
    # No security is required here. You must have already been authenticated
    # in order to get a 'login_name' variable in the session.
    try:
        return session['login_name']
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
    license_file = os.path.join(util.make_local_path("apps"),
                        "tos", "license.html")
    req.sendfile(license_file)
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

