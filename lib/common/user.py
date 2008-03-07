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

# Module: User
# Author: Matt Giuca
# Date:   19/2/2008

# Provides a User class which stores the login details of a particular IVLE
# user. Objects of this class are expected to be stored in the request
# session.

import common.caps

# Similar to db.login_fields_list but contains a different set of fields.
# The User object does not contain all the fields.
user_fields_required = frozenset((
    "login", "fullname", "role", "state", "unixid"
))
user_fields_list = (
    "login", "state", "unixid", "email", "nick", "fullname",
    "role", "studentid", "acct_exp", "pass_exp", "last_login",
    "svn_pass", "local_password",
)
# Fields not included: passhash, last_login

class UserException(Exception):
    pass

class User(object):
    """
    Stores the login details of a particular IVLE user.
    Its fields correspond to (most of) the fields of the "login" table of the
    IVLE db.
    All fields are always present, but some may be None.
    """
    __slots__ = user_fields_list
    def __init__(self, **kwargs):
        # XXX Will ignore unknown fields instead of erroring
        if "rolenm" in kwargs and "role" not in kwargs:
            kwargs['role'] = common.caps.Role(kwargs['rolenm'])
        if "passhash" in kwargs and "local_password" not in kwargs:
            kwargs['local_password'] = kwargs['passhash'] is not None
        for r in user_fields_list:
            if r in kwargs:
                self.__setattr__(r, kwargs[r])
            elif r in user_fields_required:
                # Required argument, not specified
                raise TypeError("User: Required field %s missing" % repr(r))
            else:
                # Optional arguments
                if r == "nick":
                    try:
                        self.nick = kwargs['fullname']
                    except KeyError:
                        raise TypeError("User: Required field "
                            "'fullname' missing")
                else:
                    self.__setattr__(r, None)
    def __repr__(self):
        items = ["%s=%s" % (r, repr(self.__getattribute__(r)))
            for r in user_fields_list]
        return "User(" + ', '.join(items) + ")"
    def __iter__(self):
        """Iteration yielding field:value pairs.
        (Allows the "dict" function to work on Users)
        """
        for r in user_fields_list:
            yield (r, self.__getattribute__(r))

    def hasCap(self, capability):
        """Given a capability (which is a Role object), returns True if this
        User has that capability, False otherwise.
        """
        return self.role.hasCap(capability)

    def pass_expired(self):
        """Determines whether the pass_exp field indicates that
           login should be denied.
        """
        fieldval = self.pass_exp
        return fieldval is not None and time.localtime() > fieldval
    def acct_expired(self):
        """Determines whether the acct_exp field indicates that
           login should be denied.
        """
        fieldval = self.acct_exp
        return fieldval is not None and time.localtime() > fieldval
