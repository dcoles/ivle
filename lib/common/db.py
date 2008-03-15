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
# Date:   15/2/2008

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
import copy
import time

from common import (caps, user)

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

def _escape(val):
    """Wrapper around pg.escape_string. Prepares the Python value for use in
    SQL. Returns a string, which may be safely placed verbatim into an SQL
    query.
    Handles the following types:
    * str: Escapes the string, and also quotes it.
    * int/long/float: Just converts to an unquoted string.
    * bool: Returns as "TRUE" or "FALSE", unquoted.
    * NoneType: Returns "NULL", unquoted.
    * common.caps.Role: Returns the role as a quoted, lowercase string.
    Raises a DBException if val has an unsupported type.
    """
    # "E'" is postgres's way of making "escape" strings.
    # Such strings allow backslashes to escape things. Since escape_string
    # converts a single backslash into two backslashes, it needs to be fed
    # into E mode.
    # Ref: http://www.postgresql.org/docs/8.2/static/sql-syntax-lexical.html
    # WARNING: PostgreSQL-specific code
    if val is None:
        return "NULL"
    elif isinstance(val, str):
        return "E'" + pg.escape_string(val) + "'"
    elif isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    elif isinstance(val, int) or isinstance(val, long) \
        or isinstance(val, float):
        return str(val)
    elif isinstance(val, caps.Role):
        return _escape(str(val))
    elif isinstance(val, time.struct_time):
        return _escape(time.strftime(TIMESTAMP_FORMAT, val))
    else:
        raise DBException("Attempt to insert an unsupported type "
            "into the database")

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
        self.open = False
        self.db = pg.connect(dbname=conf.db_dbname, host=conf.db_host,
                port=conf.db_port, user=conf.db_user, passwd=conf.db_password)
        self.open = True

    def __del__(self):
        if self.open:
            self.db.close()

    # GENERIC DB FUNCTIONS #

    @staticmethod
    def check_dict(dict, tablefields, disallowed=frozenset([]), must=False):
        """Checks that a dict does not contain keys that are not fields
        of the specified table.
        dict: A mapping from string keys to values; the keys are checked to
            see that they correspond to login table fields.
        tablefields: Collection of strings for field names in the table.
            Only these fields will be allowed.
        disallowed: Optional collection of strings for field names that are
            not allowed.
        must: If True, the dict MUST contain all fields in tablefields.
            If False, it may contain any subset of the fields.
        Returns True if the dict is valid, False otherwise.
        """
        allowed = frozenset(tablefields) - frozenset(disallowed)
        dictkeys = frozenset(dict.keys())
        if must:
            return allowed == dictkeys
        else:
            return allowed.issuperset(dictkeys)

    def insert(self, dict, tablename, tablefields, disallowed=frozenset([]),
        dry=False):
        """Inserts a new row in a table, using data from a supplied
        dictionary (which will be checked by check_dict).
        dict: Dictionary mapping column names to values. The values may be
            any of the following types:
            str, int, long, float, NoneType.
        tablename: String, name of the table to insert into. Will NOT be
            escaped - must be a valid identifier.
        tablefields, disallowed: see check_dict.
        dry: Returns the SQL query as a string, and does not execute it.
        Raises a DBException if the dictionary contains invalid fields.
        """
        if not DB.check_dict(dict, tablefields, disallowed):
            extras = set(dict.keys()) - tablefields
            raise DBException("Supplied dictionary contains invalid fields. (%s)" % (repr(extras)))
        # Build two lists concurrently: field names and values, as SQL strings
        fieldnames = []
        values = []
        for k,v in dict.items():
            fieldnames.append(k)
            values.append(_escape(v))
        if len(fieldnames) == 0: return
        fieldnames = ', '.join(fieldnames)
        values = ', '.join(values)
        query = ("INSERT INTO %s (%s) VALUES (%s);"
            % (tablename, fieldnames, values))
        if dry: return query
        self.db.query(query)

    def update(self, primarydict, updatedict, tablename, tablefields,
        primary_keys, disallowed_update=frozenset([]), dry=False):
        """Updates a row in a table, matching against primarydict to find the
        row, and using the data in updatedict (which will be checked by
        check_dict).
        primarydict: Dict mapping column names to values. The keys should be
            the table's primary key. Only rows which match this dict's values
            will be updated.
        updatedict: Dict mapping column names to values. The columns will be
            updated with the given values for the matched rows.
        tablename, tablefields, disallowed_update: See insert.
        primary_keys: Collection of strings which together form the primary
            key for this table. primarydict must contain all of these as keys,
            and only these keys.
        """
        if (not (DB.check_dict(primarydict, primary_keys, must=True)
            and DB.check_dict(updatedict, tablefields, disallowed_update))):
            raise DBException("Supplied dictionary contains invalid or missing fields (1).")
        # Make a list of SQL fragments of the form "field = 'new value'"
        # These fragments are ALREADY-ESCAPED
        setlist = []
        for k,v in updatedict.items():
            setlist.append("%s = %s" % (k, _escape(v)))
        wherelist = []
        for k,v in primarydict.items():
            wherelist.append("%s = %s" % (k, _escape(v)))
        if len(setlist) == 0 or len(wherelist) == 0:
            return
        # Join the fragments into a comma-separated string
        setstring = ', '.join(setlist)
        wherestring = ' AND '.join(wherelist)
        # Build the whole query as an UPDATE statement
        query = ("UPDATE %s SET %s WHERE %s;"
            % (tablename, setstring, wherestring))
        if dry: return query
        self.db.query(query)

    def delete(self, primarydict, tablename, primary_keys, dry=False):
        """Deletes a row in the table, matching against primarydict to find
        the row.
        primarydict, tablename, primary_keys: See update.
        """
        if not DB.check_dict(primarydict, primary_keys, must=True):
            raise DBException("Supplied dictionary contains invalid or missing fields (2).")
        wherelist = []
        for k,v in primarydict.items():
            wherelist.append("%s = %s" % (k, _escape(v)))
        if len(wherelist) == 0:
            return
        wherestring = ' AND '.join(wherelist)
        query = ("DELETE FROM %s WHERE %s;" % (tablename, wherestring))
        if dry: return query
        self.db.query(query)

    def get_single(self, primarydict, tablename, getfields, primary_keys,
        error_notfound="No rows found", dry=False):
        """Retrieves a single row from a table, returning it as a dictionary
        mapping field names to values. Matches against primarydict to find the
        row.
        primarydict, tablename, primary_keys: See update/delete.
        getfields: Collection of strings; the field names which will be
            returned as keys in the dictionary.
        error_notfound: Error message if 0 rows match.
        Raises a DBException if 0 rows match, with error_notfound as the msg.
        Raises an AssertError if >1 rows match (this should not happen if
            primary_keys is indeed the primary key).
        """
        if not DB.check_dict(primarydict, primary_keys, must=True):
            raise DBException("Supplied dictionary contains invalid or missing fields (3).")
        wherelist = []
        for k,v in primarydict.items():
            wherelist.append("%s = %s" % (k, _escape(v)))
        if len(getfields) == 0 or len(wherelist) == 0:
            return
        # Join the fragments into a comma-separated string
        getstring = ', '.join(getfields)
        wherestring = ' AND '.join(wherelist)
        # Build the whole query as an SELECT statement
        query = ("SELECT %s FROM %s WHERE %s;"
            % (getstring, tablename, wherestring))
        if dry: return query
        result = self.db.query(query)
        # Expecting exactly one
        if result.ntuples() != 1:
            # It should not be possible for ntuples to be greater than 1
            assert (result.ntuples() < 1)
            raise DBException(error_notfound)
        # Return as a dictionary
        return result.dictresult()[0]

    def get_all(self, tablename, getfields, dry=False):
        """Retrieves all rows from a table, returning it as a list of
        dictionaries mapping field names to values.
        tablename, getfields: See get_single.
        """
        if len(getfields) == 0:
            return
        getstring = ', '.join(getfields)
        query = ("SELECT %s FROM %s;" % (getstring, tablename))
        if dry: return query
        return self.db.query(query).dictresult()

    def start_transaction(self, dry=False):
        """Starts a DB transaction.
        Will not commit any changes until self.commit() is called.
        """
        query = "START TRANSACTION;"
        if dry: return query
        self.db.query(query)

    def commit(self, dry=False):
        """Commits (ends) a DB transaction.
        Commits all changes since the call to start_transaction.
        """
        query = "COMMIT;"
        if dry: return query
        self.db.query(query)

    def rollback(self, dry=False):
        """Rolls back (ends) a DB transaction, undoing all changes since the
        call to start_transaction.
        """
        query = "ROLLBACK;"
        if dry: return query
        self.db.query(query)

    # USER MANAGEMENT FUNCTIONS #

    login_primary = frozenset(["login"])
    login_fields_list = [
        "login", "passhash", "state", "unixid", "email", "nick", "fullname",
        "rolenm", "studentid", "acct_exp", "pass_exp", "last_login", "svn_pass"
    ]
    login_fields = frozenset(login_fields_list)

    def create_user(self, user_obj=None, dry=False, **kwargs):
        """Creates a user login entry in the database.
        Two ways to call this - passing a user object, or passing
        all fields as separate arguments.

        Either pass a "user_obj" as the first argument (in which case other
        fields will be ignored), or pass all fields as arguments.

        All user fields are to be passed as args. The argument names
        are the field names of the "login" table of the DB schema.
        However, instead of supplying a "passhash", you must supply a
        "password" argument, which will be hashed internally.
        Also "state" must not given explicitly; it is implicitly set to
        "no_agreement".
        Raises an exception if the user already exists, or the dict contains
        invalid keys or is missing required keys.
        """
        if 'passhash' in kwargs:
            raise DBException("Supplied arguments include passhash (invalid) (1).")
        # Make a copy of the dict. Change password to passhash (hashing it),
        # and set 'state' to "no_agreement".
        if user_obj is None:
            # Use the kwargs
            fields = copy.copy(kwargs)
        else:
            # Use the user object
            fields = dict(user_obj)
        if 'password' in fields:
            fields['passhash'] = _passhash(fields['password'])
            del fields['password']
        if 'role' in fields:
            # Convert role to rolenm
            fields['rolenm'] = str(user_obj.role)
            del fields['role']
        if user_obj is None:
            fields['state'] = "no_agreement"
            # else, we'll trust the user, but it SHOULD be "no_agreement"
            # (We can't change it because then the user object would not
            # reflect the DB).
        if 'local_password' in fields:
            del fields['local_password']
        # Execute the query.
        return self.insert(fields, "login", self.login_fields, dry=dry)

    def update_user(self, login, dry=False, **kwargs):
        """Updates fields of a particular user. login is the name of the user
        to update. The dict contains the fields which will be modified, and
        their new values. If any value is omitted from the dict, it does not
        get modified. login and studentid may not be modified.
        Passhash may be modified by supplying a "password" field, in
        cleartext, not a hashed password.

        Note that no checking is done. It is expected this function is called
        by a trusted source. In particular, it allows the password to be
        changed without knowing the old password. The caller should check
        that the user knows the existing password before calling this function
        with a new one.
        """
        if 'passhash' in kwargs:
            raise DBException("Supplied arguments include passhash (invalid) (2).")
        if "password" in kwargs:
            kwargs = copy.copy(kwargs)
            kwargs['passhash'] = _passhash(kwargs['password'])
            del kwargs['password']
        return self.update({"login": login}, kwargs, "login",
            self.login_fields, self.login_primary, ["login", "studentid"],
            dry=dry)

    def get_user(self, login, dry=False):
        """Given a login, returns a User object containing details looked up
        in the DB.

        Raises a DBException if the login is not found in the DB.
        """
        userdict = self.get_single({"login": login}, "login",
            self.login_fields, self.login_primary,
            error_notfound="get_user: No user with that login name", dry=dry)
        if dry:
            return userdict     # Query string
        # Package into a User object
        return user.User(**userdict)

    def get_users(self, dry=False):
        """Returns a list of all users in the DB, as User objects.
        """
        userdicts = self.get_all("login", self.login_fields, dry=dry)
        if dry:
            return userdicts    # Query string
        # Package into User objects
        return [user.User(**userdict) for userdict in userdicts]

    def get_user_loginid(self, login, dry=False):
        """Given a login, returns the integer loginid for this user.

        Raises a DBException if the login is not found in the DB.
        """
        userdict = self.get_single({"login": login}, "login",
            ['loginid'], self.login_primary,
            error_notfound="get_user_loginid: No user with that login name",
            dry=dry)
        if dry:
            return userdict     # Query string
        return userdict['loginid']

    def user_authenticate(self, login, password, dry=False):
        """Performs a password authentication on a user. Returns True if
        "passhash" is the correct passhash for the given login, False
        if the passhash does not match the password in the DB,
        and None if the passhash in the DB is NULL.
        Also returns False if the login does not exist (so if you want to
        differentiate these cases, use get_user and catch an exception).
        """
        query = "SELECT passhash FROM login WHERE login = '%s';" % login
        if dry: return query
        result = self.db.query(query)
        if result.ntuples() == 1:
            # Valid username. Check password.
            passhash = result.getresult()[0][0]
            if passhash is None:
                return None
            return _passhash(password) == passhash
        else:
            return False

    # PROBLEM AND PROBLEM ATTEMPT FUNCTIONS #

    def get_problem_problemid(self, exercisename, dry=False):
        """Given an exercise name, returns the associated problemID.
        If the exercise name is NOT in the database, it inserts it and returns
        the new problemID. Hence this may mutate the DB, but is idempotent.
        """
        try:
            d = self.get_single({"identifier": exercisename}, "problem",
                ['problemid'], frozenset(["identifier"]),
                dry=dry)
            if dry:
                return d        # Query string
        except DBException:
            if dry:
                # Shouldn't try again, must have failed for some other reason
                raise
            # if we failed to get a problemid, it was probably because
            # the exercise wasn't in the db. So lets insert it!
            #
            # The insert can fail if someone else simultaneously does
            # the insert, so if the insert fails, we ignore the problem. 
            try:
                self.insert({'identifier': exercisename}, "problem",
                        frozenset(['identifier']))
            except Exception, e:
                pass

            # Assuming the insert succeeded, we should be able to get the
            # problemid now.
            d = self.get_single({"identifier": exercisename}, "problem",
                ['problemid'], frozenset(["identifier"]))

        return d['problemid']

    def insert_problem_attempt(self, login, exercisename, date, complete,
        attempt, dry=False):
        """Inserts the details of a problem attempt into the database.
        exercisename: Name of the exercise. (identifier field of problem
            table). If this exercise does not exist, also creates a new row in
            the problem table for this exercise name.
        login: Name of the user submitting the attempt. (login field of the
            login table).
        date: struct_time, the date this attempt was made.
        complete: bool. Whether the test passed or not.
        attempt: Text of the attempt.

        Note: Even if dry, will still physically call get_problem_problemid,
        which may mutate the DB, and get_user_loginid, which may fail.
        """
        problemid = self.get_problem_problemid(exercisename)
        loginid = self.get_user_loginid(login)  # May raise a DBException

        return self.insert({
                'problemid': problemid,
                'loginid': loginid,
                'date': date,
                'complete': complete,
                'attempt': attempt,
            }, 'problem_attempt',
            frozenset(['problemid','loginid','date','complete','attempt']),
            dry=dry)

    def get_problem_attempt_last_text(self, login, exercisename, dry=False):
        """Given a login name and exercise name, returns the text of the
        last submitted attempt for this question. Returns None if the user has
        not made an attempt on this problem.

        Note: Even if dry, will still physically call get_problem_problemid,
        which may mutate the DB, and get_user_loginid, which may fail.
        """
        problemid = self.get_problem_problemid(exercisename)
        loginid = self.get_user_loginid(login)  # May raise a DBException
        # "Get the single newest attempt made by this user for this problem"
        query = ("SELECT attempt FROM problem_attempt "
            "WHERE loginid = %d AND problemid = %d "
            "ORDER BY date DESC "
            "LIMIT 1;" % (loginid, problemid))
        if dry: return query
        result = self.db.query(query)
        if result.ntuples() == 1:
            # The user has made at least 1 attempt. Return the newest.
            return result.getresult()[0][0]
        else:
            return None

    def close(self):
        """Close the DB connection. Do not call any other functions after
        this. (The behaviour of doing so is undefined).
        """
        self.db.close()
        self.open = False
