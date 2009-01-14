# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
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

# Author: Matt Giuca, Will Grant

"""
Database Classes and Utilities for Storm ORM

This module provides all of the classes which map to database tables.
It also provides miscellaneous utility functions for database interaction.
"""

from storm.locals import create_database, Store, Int, Unicode, DateTime, \
                         Reference

import ivle.conf
import ivle.caps

def get_conn_string():
    """
    Returns the Storm connection string, generated from the conf file.
    """
    return "postgres://%s:%s@%s:%d/%s" % (ivle.conf.db_user,
        ivle.conf.db_password, ivle.conf.db_host, ivle.conf.db_port,
        ivle.conf.db_dbname)

def get_store():
    """
    Open a database connection and transaction. Return a storm.store.Store
    instance connected to the configured IVLE database.
    """
    return Store(create_database(get_conn_string()))

class User(object):
    """
    Represents an IVLE user.
    """
    __storm_table__ = "login"

    id = Int(primary=True, name="loginid")
    login = Unicode()
    passhash = Unicode()
    state = Unicode()
    rolenm = Unicode()
    unixid = Int()
    nick = Unicode()
    pass_exp = DateTime()
    acct_exp = DateTime()
    last_login = DateTime()
    svn_pass = Unicode()
    email = Unicode()
    fullname = Unicode()
    studentid = Unicode()
    settings = Unicode()

    def _get_role(self):
        if self.rolenm is None:
            return None
        return ivle.caps.Role(self.rolenm)
    def _set_role(self, value):
        if not isinstance(value, ivle.caps.Role):
            raise TypeError("role must be an ivle.caps.Role")
        self.rolenm = unicode(value)
    role = property(_get_role, _set_role)

    def __init__(self, **kwargs):
        """
        Create a new User object. Supply any columns as a keyword argument.
        """
        for k,v in kwargs.items():
            if k.startswith('_') or not hasattr(self, k):
                raise TypeError("User got an unexpected keyword argument '%s'"
                    % k)
            setattr(self, k, v)

    def __repr__(self):
        return "<%s '%s'>" % (type(self).__name__, self.login)

    def has_cap(self, capability):
        """Given a capability (which is a Role object), returns True if this
        User has that capability, False otherwise.
        """
        return self.role.hasCap(capability)

    # XXX Should be @property
    def pass_expired(self):
        """Determines whether the pass_exp field indicates that
           login should be denied.
        """
        fieldval = self.pass_exp
        return fieldval is not None and time.localtime() > fieldval
    # XXX Should be @property
    def acct_expired(self):
        """Determines whether the acct_exp field indicates that
           login should be denied.
        """
        fieldval = self.acct_exp
        return fieldval is not None and time.localtime() > fieldval
