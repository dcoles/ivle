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

# Module: authenticate
# Author: Matt Giuca
# Date:   1/2/2008

# Provides a mechanism for authenticating a username and password, and
# returning a yes/no response.

import common.db

def authenticate(username, password):
    """Determines whether a particular username/password combination is
    valid. The password is in cleartext.

    Returns None if failed to authenticate.
    Returns a dictionary containing the user's login fields (including
    "login", "nick" and "fullname") on success.
    """

    # TODO.
    # Just authenticate against the DB at the moment.
    # Later we will provide other auth options such as LDAP.

    # WARNING: Both username and password may contain any characters, and must
    # be sanitized within this function.
    # (Not SQL-sanitized, just sanitized to our particular constraints).

    # Spawn a DB object just for making this call.
    # (This should not spawn a DB connection on each page reload, only when
    # there is no session object to begin with).
    dbconn = common.db.DB()
    try:
        if not dbconn.user_authenticate(username, password):
            return None
        return dbconn.get_user(username)
    finally:
        dbconn.close()
