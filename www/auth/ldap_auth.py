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

# Module: LDAP Authenticate
# Author: Matt Giuca
# Date:   21/2/2008

# Pluggable authentication module for LDAP servers.
# This will read the ldap_url and ldap_format_string config variables.
# This module is NOT active implicitly - it must be specified in the
# "auth_modules" config string.
# However, setup.py should configure it in auth_modules by default.

import autherror
import conf
import ldap

def auth(dbconn, login, password, user):
    """
    A plugin auth function, as described above.
    This one authenticates against an LDAP server.
    Returns user if successful. Raises AuthError if unsuccessful.
    Also raises AuthError if the LDAP server had an unexpected error.
    """
    try:
        l = ldap.initialize(conf.ldap_url)
        # ldap_format_string contains a "%s" to put the login name
        l.simple_bind_s(conf.ldap_format_string % login, password)
    except ldap.INVALID_CREDENTIALS:
        raise AuthError()
    except Exception, msg:
        raise AuthError("Internal error (LDAP auth): %s" % repr(msg))
    # Got here - Must have successfully authenticated with LDAP
    return user

