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
    """
    # "E'" is postgres's way of making "escape" strings.
    # Such strings allow backslashes to escape things. Since escape_string
    # converts a single backslash into two backslashes, it needs to be fed
    # into E mode.
    # Ref: http://www.postgresql.org/docs/8.2/static/sql-syntax-lexical.html
    # WARNING: PostgreSQL-specific code
    return "E'" + pg.escape_string(str) + "'"

def _passhash(password):
    return md5.md5(password).hexdigest()

class DB:
    """An IVLE database object. This object provides an interface to
    interacting with the IVLE database without using any external SQL.

    Most methods of this class have an optional dry argument. If true, they
    will return the SQL query string and NOT actually execute it. (For
    debugging purposes).
    """
    def __init__(self):
        """Connects to the database and creates a DB object.
        Takes no parameters - gets all the DB info from the configuration."""
        self.db = pg.connect(dbname=conf.db_dbname, host=conf.db_host,
                port=conf.db_port, user=conf.db_user, passwd=conf.db_password)

    # USER MANAGEMENT FUNCTIONS #

    def create_user(self, login, password, nick, fullname, rolenm, studentid,
        dry=False):
        """Creates a user login entry in the database.
        Arguments are the same as those in the "login" table of the schema.
        The exception is "password", which is a cleartext password. makeuser
        will hash the password.
        """
        passhash = _passhash(password)
        query = ("INSERT INTO login (login, passhash, nick, fullname, "
            "rolenm, studentid) VALUES (%s, %s, %s, %s, %s, %s);" %
            (_escape(login), _escape(passhash), _escape(nick),
            _escape(fullname), _escape(rolenm), _escape(studentid)))
        if dry: return query
        self.db.query(query)

    def update_user(self, login, new_password=None, new_nick=None,
        new_fullname=None, new_rolenm=None, dry=False):
        """Updates fields of a particular user. login is the name of the user
        to update. The other arguments are optional fields which may be
        modified. If None or omitted, they do not get modified. login and
        studentid may not be modified."""
        # Make a list of SQL fragments of the form "field = 'new value'"
        # These fragments are ALREADY-ESCAPED
        setlist = []
        if new_password is not None:
            setlist.append("passhash = " + _escape(_passhash(new_password)))
        if new_nick is not None:
            setlist.append("nick = " + _escape(new_nick))
        if new_fullname is not None:
            setlist.append("fullname = " + _escape(new_fullname))
        if new_rolenm is not None:
            setlist.append("rolenm = " + _escape(new_rolenm))
        if len(setlist) == 0:
            return
        # Join the fragments into a comma-separated string
        setstring = ', '.join(setlist)
        # Build the whole query as an UPDATE statement
        query = ("UPDATE login SET %s WHERE login = %s;"
            % (setstring, _escape(login)))
        if dry: return query
        self.db.query(query)

    def drop_user(self, login, dry=False):
        """Deletes a user login entry from the database."""
        query = "DELETE FROM login WHERE login = %s;" % _escape(login)
        if dry: return query
        self.db.query(query)

    def close(self):
        """Close the DB connection. Do not call any other functions after
        this. (The behaviour of doing so is undefined).
        """
        self.db.close()
