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

from mod_python import (util, Session)

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
        return session['login_name']
    except KeyError:
        pass

    badlogin = False
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
                badlogin = True
            else:
                login_details = \
                    authenticate.authenticate(username.value, password.value)
                if login_details is None:
                    badlogin = True
                else:
                    # Success - Set the session and redirect to avoid POSTDATA
                    session['login_name'] = username.value
                    session['nick'] = login_details['nick']
                    session['fullname'] = login_details['fullname']
                    session['rolenm'] = login_details['rolenm']
                    session['studentid'] = login_details['studentid']
                    session.save()
                    req.throw_redirect(req.uri)

    # User is not logged in. Present the login box.
    # Give a 403 Forbidden status, but present a full HTML login page
    # instead of the usual 403 error.
    req.status = req.HTTP_FORBIDDEN
    req.content_type = "text/html"
    req.title = "Login"
    req.write_html_head_foot = True

    # Write the HTML for the login page
    # If badlogin, display an error message indicating a failed login
    req.write("""<div id="ivle_padding">
<p>Welcome to the Informatics Virtual Learning Environment.
   Please log in to access your files and assessment.</p>""")
    if badlogin:
        req.write("""<p class="error">Invalid username or password.</p>""")
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
