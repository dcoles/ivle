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

# Module: Database
# Author: Matt Giuca
# Date:   1/2/2008

# Code to talk to the PostgreSQL database.
# (This is the Data Access Layer).
# All DB code should be in this module to ensure portability if we want to
# change the DB implementation.
# This means no SQL strings should be outside of this module. Add functions
# here to perform the activities needed, and place the SQL code for those
# activities within.

# CAUTION to editors of this module.
# All string inputs must be sanitized by calling _escape before being
# formatted into an SQL query string.

import pg
import conf
import md5

def _escape(str):
    """Wrapper around pg.escape_string. Escapes the string for use in SQL, and
    also quotes it to make sure that every string used in a query is quoted.
    If str is None, returns "NULL", which is unescaped and thus a valid SQL
    value.
    """
    # "E'" is postgres's way of making "escape" strings.
    # Such strings allow backslashes to escape things. Since escape_string
    # converts a single backslash into two backslashes, it needs to be fed
    # into E mode.
    # Ref: http://www.postgresql.org/docs/8.2/static/sql-syntax-lexical.html
    # WARNING: PostgreSQL-specific code
    if str is None:
        return "NULL"
    return "E'" + pg.escape_string(str) + "'"

def _passhash(password):
    return md5.md5(password).hexdigest()

class DBException(Exception):
    """A DBException is for bad conditions in the database or bad input to
    these methods. If Postgres throws an exception it does not get rebadged.
    This is only for additional exceptions."""
    pass

class DB:
    """An IVLE database object. This object provides an interface to
    interacting with the IVLE database without using any external SQL.

    Most methods of this class have an optional dry argument. If true, they
    will return the SQL query string and NOT actually execute it. (For
    debugging purposes).

    Methods may throw db.DBException, or any of the pg exceptions as well.
    (In general, be prepared to catch exceptions!)
    """
    def __init__(self):
        """Connects to the database and creates a DB object.
        Takes no parameters - gets all the DB info from the configuration."""
        self.db = pg.connect(dbname=conf.db_dbname, host=conf.db_host,
                port=conf.db_port, user=conf.db_user, passwd=conf.db_password)

    # USER MANAGEMENT FUNCTIONS #

    def create_user(self, login, unixid, password, nick, fullname, rolenm,
        studentid, dry=False):
        """Creates a user login entry in the database.
        Arguments are the same as those in the "login" table of the schema.
        The exception is "password", which is a cleartext password. makeuser
        will hash the password.
        Raises an exception if the user already exists.
        """
        passhash = _passhash(password)
        query = ("INSERT INTO login (login, unixid, passhash, nick, fullname,"
            " rolenm, studentid) VALUES (%s, %d, %s, %s, %s, %s, %s);" %
            (_escape(login), unixid, _escape(passhash), _escape(nick),
            _escape(fullname), _escape(rolenm), _escape(studentid)))
        if dry: return query
        self.db.query(query)

    def update_user(self, login, password=None, nick=None,
        fullname=None, rolenm=None, dry=False):
        """Updates fields of a particular user. login is the name of the user
        to update. The other arguments are optional fields which may be
        modified. If None or omitted, they do not get modified. login and
        studentid may not be modified.

        Note that no checking is done. It is expected this function is called
        by a trusted source. In particular, it allows the password to be
        changed without knowing the old password. The caller should check
        that the user knows the existing password before calling this function
        with a new one.
        """
        # Make a list of SQL fragments of the form "field = 'new value'"
        # These fragments are ALREADY-ESCAPED
        setlist = []
        if password is not None:
            setlist.append("passhash = " + _escape(_passhash(password)))
        if nick is not None:
            setlist.append("nick = " + _escape(nick))
        if fullname is not None:
            setlist.append("fullname = " + _escape(fullname))
        if rolenm is not None:
            setlist.append("rolenm = " + _escape(rolenm))
        if len(setlist) == 0:
            return
        # Join the fragments into a comma-separated string
        setstring = ', '.join(setlist)
        # Build the whole query as an UPDATE statement
        query = ("UPDATE login SET %s WHERE login = %s;"
            % (setstring, _escape(login)))
        if dry: return query
        self.db.query(query)

    def delete_user(self, login, dry=False):
        """Deletes a user login entry from the database."""
        query = "DELETE FROM login WHERE login = %s;" % _escape(login)
        if dry: return query
        self.db.query(query)

    def get_user(self, login, dry=False):
        """Given a login, returns a dictionary of the user's DB fields,
        excluding the passhash field.

        Raises a DBException if the login is not found in the DB.
        """
        query = ("SELECT login, unixid, nick, fullname, rolenm, studentid "
            "FROM login WHERE login = %s;" % _escape(login))
        if dry: return query
        result = self.db.query(query)
        # Expecting exactly one
        if result.ntuples() != 1:
            # It should not be possible for ntuples to be greater than 1
            assert (result.ntuples() < 1)
            raise DBException("get_user: No user with that login name")
        # Return as a dictionary
        return result.dictresult()[0]

    def get_users(self, dry=False):
        """Returns a list of all users. The list elements are a dictionary of
        the user's DB fields, excluding the passhash field.
        """
        query = ("SELECT login, unixid, nick, fullname, rolenm, studentid "
            "FROM login")
        if dry: return query
        return self.db.query(query).dictresult()

    def user_authenticate(self, login, password, dry=False):
        """Performs a password authentication on a user. Returns True if
        "password" is the correct password for the given login, False
        otherwise. "password" is cleartext.
        Also returns False if the login does not exist (so if you want to
        differentiate these cases, use get_user and catch an exception).
        """
        query = ("SELECT login FROM login "
            "WHERE login = '%s' AND passhash = %s;"
            % (login, _escape(_passhash(password))))
        if dry: return query
        result = self.db.query(query)
        # If one row was returned, succeed.
        # Otherwise, fail to authenticate.
        return result.ntuples() == 1

    def close(self):
        """Close the DB connection. Do not call any other functions after
        this. (The behaviour of doing so is undefined).
        """
        self.db.close()
