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
# Date:   19/2/2008

# Provides a mechanism for authenticating a username and password, and
# returning a yes/no response.

# Has a plugin interface for authentication modules.
# An authentication module is a Python module with an "auth" function,
# which accepts 3 positional arguments.
# plugin_module.auth(dbconn, login, password, user)
# dbconn is an open connection to the IVLE database.
# login and password are required strings, password is cleartext.
# user is a User object or None.
# If it's a User object, it must return the same object if it returns a user.
# This object should describe the user logging in.
# It may be None if the user is not known to this DB.
# Returns either a User object or None, or raises an AuthError.
# Returning a User object implies success, and also gives details about the
# user if none were known to the DB (such details will be written to the DB).
# Returning None implies a soft failure, and that another auth method should
# be found.
# Raising an AuthError implies a hard failure, with an appropriate error
# message. No more auth will be done.

from autherror import AuthError
import conf
import common.db
import common.user

import sys
import os

def authenticate(login, password):
    """Determines whether a particular login/password combination is
    valid. The password is in cleartext.

    Returns a User object containing the user's details on success.
    Raises an AuthError containing an appropriate error message on failure.

    The User returned is guaranteed to be in the IVLE database.
    This could be from reading or writing to the DB. If authenticate can't
    find the user in the DB, it may get user data from some other source
    (such as LDAP) and actually write it to the DB before returning.
    """
    # WARNING: Both username and password may contain any characters, and must
    # be sanitized within this function.
    # (Not SQL-sanitized, just sanitized to our particular constraints).
    # TODO Sanitize username

    # Spawn a DB object just for making this call.
    # (This should not spawn a DB connection on each page reload, only when
    # there is no session object to begin with).
    dbconn = common.db.DB()

    try:
        user = dbconn.get_user(login)
    except common.db.DBException:
        # If our attempt to get the named user from the db fails,
        # then set user to None.
        # We may still auth (eg. by pulling details from elsewhere and writing
        # to DB).
        user = None
    try:
        for modname, m in auth_modules:
            # May raise an AuthError - allow to propagate
            auth_result = m(dbconn, login, password, user)
            if auth_result is None:
                # Can't auth with this module; try another
                pass
            elif auth_result == False:
                return None
            elif isinstance(auth_result, common.user.User):
                if user is not None and auth_result is not user:
                    # If user is not None, then it must return the same user
                    raise AuthError("Internal error: "
                        "Bad authentication module %s (changed user)"
                        % repr(modname))
                elif user is None:
                    # We just got ourselves some user details from an external
                    # source. Put them in the DB.
                    dbconn.create_user(auth_result)
                    pass
                return auth_result
            else:
                raise AuthError("Internal error: "
                    "Bad authentication module %s (bad return type)"
                    % repr(modname))
        # No auths checked out; fail.
        raise AuthError()
    finally:
        dbconn.close()

def simple_db_auth(dbconn, login, password, user):
    """
    A plugin auth function, as described above.
    This one just authenticates against the local database.
    Returns None if the password in the DB is NULL, indicating that another
    auth method should be used.
    Raises an AuthError if mismatched, indicating failure to auth.
    """
    if user is None:
        # The login doesn't exist. Therefore return None so we can try other
        # means of authentication.
        return None
    auth_result = dbconn.user_authenticate(login, password)
    # auth_result is either True, False (fail) or None (try another)
    if auth_result is None:
        return None
    elif auth_result:
        return user
    else:
        raise AuthError()

# Allow imports to get files from this directory.
# Get the directory that this module (authenticate) is in
authpath = os.path.split(sys.modules[__name__].__file__)[0]
# Add it to sys.path
sys.path.append(authpath)

# Create a global variable "auth_modules", a list of (name, function object)s.
# This list consists of simple_db_auth, plus the "auth" functions of all the
# plugin auth modules.

auth_modules = [("simple_db_auth", simple_db_auth)]
for modname in conf.auth_modules.split(','):
    try:
        mod = __import__(modname)
    except ImportError:
        raise AuthError("Internal error: Can't import auth module %s"
            % repr(modname))
    try:
        authfunc = mod.auth
    except AttributeError:
        raise AuthError("Internal error: Auth module %s has no 'auth' "
            "function" % repr(modname))
    auth_modules.append((modname, authfunc))
