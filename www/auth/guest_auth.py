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

# Module: Guest Authenticate
# Author: Matt Giuca
# Date:   21/2/2008

# Pluggable authentication module for LDAP servers.
# This module is part-test part-something-you-may-want.
# If enabled, it allows "external auth" against an account "guest" with
# password "guest".
# It may be called with a None user, and will return a guest User object,
# which will mean it gets put in the database.
# Thus it behaves similarly to a module which retrieves user details from an
# external source like LDAP.
# This module is NOT active implicitly - it must be specified in the
# "auth_modules" config string.

from autherror import AuthError
from common.user import User
from common.caps import Role

# XXX: What to put here
GUEST_UID = 4000

def auth(dbconn, login, password, user):
    """
    A plugin auth function, as described above.
    This one authenticates against a "guest"/"guest" account.
    Returns user if successful. Raises AuthError if unsuccessful.
    Returns a new User object if user is None.
    """
    if login != "guest" or password != "guest":
        raise AuthError()

    if user is not None:
        return user

    # Create a guest user
    return User(login="guest", fullname="Guest Account", nick="Guest",
        role=Role.ANYONE, state="no_agreement", unixid=GUEST_UID)
