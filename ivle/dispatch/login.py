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
import datetime

try:
    import mod_python.Cookie
except ImportError:
    # This needs to be importable from outside Apache.
    pass

import ivle.conf
from ivle import (util, caps)
from ivle.auth import authenticate, AuthError
from ivle.webapp.base.plugins import CookiePlugin
import ivle.database


# XXX: Move this elsewhere, as it's just in storage now...
def tos_stuff():
    # User is not logged in or their account is not enabled.
    if user is not None:
        # Only possible if no errors occured thus far
        if user.state == "no_agreement":
            # User has authenticated but has not accepted the TOS.
            # Present them with the TOS page.
            # First set their username for display at the top, but make sure
            # the apps tabs are not displayed
            req.user = user
            # IMPORTANT NOTE FOR HACKERS: You can't simply disable this check
            # if you are not planning to display a TOS page - the TOS
            # acceptance process actually calls usermgt to create the user
            # jails and related stuff.
            present_tos(req, user.fullname)
            return None
        elif user.state == "disabled":
            # User has authenticated but their account is disabled
            badlogin = "Your account has been disabled."
        elif user.state == "pending":
            # FIXME: this isn't quite the right answer, but it
            # should be more robust in the short term.
            session = req.get_session()
            session.invalidate()
            session.delete()
            user.state = u'no_agreement'
            req.store.commit()
            req.throw_redirect(req.uri)

def get_user_details(req):
    """Gets the name of the logged in user, without presenting a login box
    or attempting to authenticate.
    Returns None if there is no user logged in.
    """
    session = req.get_session()

    # Check the session to see if someone is logged in. If so, go with it.
    try:
        login = session['login']
    except KeyError:
        return None

    # Get the full User object from the db associated with this login
    return ivle.database.User.get_by_login(req.store, login)

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
    req.write(util.get_terms_of_service())
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

