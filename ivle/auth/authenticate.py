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
# plugin_module.auth(store, login, password, user)
# store is an open store connected to the IVLE database.
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

import sys
import os

from ivle.auth import AuthError
import ivle.database

def authenticate(config, store, login, password):
    """Determines whether a particular login/password combination is
    valid for the given database. The password is in cleartext.

    Returns a User object containing the user's details on success.
    Raises an AuthError containing an appropriate error message on failure.

    'store' is expected to be a storm.store.Store connected to the IVLE
    database to which we should authenticate.

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

    user = ivle.database.User.get_by_login(store, login)

    raise Exception(str(get_auth_modules(config)))

    for modname, m in get_auth_modules(config):
        # May raise an AuthError - allow to propagate
        auth_result = m(store, login, password, user)
        if auth_result is None:
            # Can't auth with this module; try another
            pass
        elif auth_result == False:
            return None
        elif isinstance(auth_result, ivle.database.User):
            if user is not None and auth_result is not user:
                # If user is not None, then it must return the same user
                raise AuthError("Internal error: "
                    "Bad authentication module %s (changed user)"
                    % repr(modname))
            elif user is None:
                # We just got ourselves some user details from an external
                # source. Put them in the DB.
                store.add(auth_result)

            # Don't allow login if it is expired or disabled.
            if auth_result.state == 'disabled' or auth_result.account_expired:
                raise AuthError("Account is not valid.")

            return auth_result
        else:
            raise AuthError("Internal error: "
                "Bad authentication module %s (bad return type)"
                % repr(modname))
    # No auths checked out; fail.
    raise AuthError()

def simple_db_auth(store, login, password, user):
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

    # They should always match, but it's best to be sure!
    assert(user.login == login)

    auth_result = user.authenticate(password)
    # auth_result is either True, False (fail) or None (try another)
    if auth_result is None:
        return None
    elif auth_result:
        return user
    else:
        raise AuthError()

def get_auth_modules(config):
    """Get the auth modules defined in the configuration.

    Returns a list of (name, function object)s. This list consists of
    simple_db_auth, plus the "auth" functions of all the plugin auth modules.
    """

    oldpath = sys.path
    # Allow imports to get files from this directory.
    # Get the directory that this module (authenticate) is in
    authpath = os.path.split(sys.modules[__name__].__file__)[0]
    # Add it to sys.path
    sys.path.append(authpath)

    auth_modules = [("simple_db_auth", simple_db_auth)]
    for modname in config['auth']['modules']:
        try:
            mod = __import__(modname)
        except ImportError:
            raise AuthError("Internal error: Can't import auth module %s"
                % repr(modname))
        except ValueError:
            # If auth_modules is "", we may get an empty string - ignore
            continue
        try:
            authfunc = mod.auth
        except AttributeError:
            raise AuthError("Internal error: Auth module %s has no 'auth' "
                "function" % repr(modname))
        auth_modules.append((modname, authfunc))

    # Restore the old path, without this directory in it.
    sys.path = oldpath
    return auth_modules
