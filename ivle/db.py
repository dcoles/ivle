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
import md5
import copy
import time

import ivle.conf
from ivle import caps

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
    * time.struct_time: Returns the time as a quoted string for insertion into
        a TIMESTAMP column.
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
    elif isinstance(val, str) or isinstance(val, unicode):
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
            "into the database (%s)" % repr(type(val)))

def _parse_boolean(val):
    """
    Accepts a boolean as output from the DB (either the string 't' or 'f').
    Returns a boolean value True or False.
    Also accepts other values which mean True or False in PostgreSQL.
    If none match, raises a DBException.
    """
    # On a personal note, what sort of a language allows 7 different values
    # to denote each of True and False?? (A: SQL)
    if isinstance(val, bool):
        return val
    elif val == 't':
        return True
    elif val == 'f':
        return False
    elif val == 'true' or val == 'y' or val == 'yes' or val == '1' \
        or val == 1:
        return True
    elif val == 'false' or val == 'n' or val == 'no' or val == '0' \
        or val == 0:
        return False
    else:
        raise DBException("Invalid boolean value returned from DB")

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
        self.db = pg.connect(host=ivle.conf.db_host, port=ivle.conf.db_port,
                         dbname=ivle.conf.db_dbname,
                         user=ivle.conf.db_user, passwd=ivle.conf.db_password)
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

    def return_insert(self, dict, tablename, tablefields, returning,
        disallowed=frozenset([]), dry=False):
        """Inserts a new row in a table, using data from a supplied
        dictionary (which will be checked by check_dict) and returns certain 
        fields as a dict.
        dict: Dictionary mapping column names to values. The values may be
            any of the following types:
            str, int, long, float, NoneType.
        tablename: String, name of the table to insert into. Will NOT be
            escaped - must be a valid identifier.
        returning: List of fields to return, not escaped
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
        returns = ', '.join(returning)
        query = ("INSERT INTO %s (%s) VALUES (%s) RETURNING (%s);"
            % (tablename, fieldnames, values, returns))
        if dry: return query
        return self.db.query(query)


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

    def insert_problem_attempt(self, user, exercisename, date, complete,
        attempt, dry=False):
        """Inserts the details of a problem attempt into the database.
        exercisename: Name of the exercise. (identifier field of problem
            table). If this exercise does not exist, also creates a new row in
            the problem table for this exercise name.
        user: The user submitting the attempt.
        date: struct_time, the date this attempt was made.
        complete: bool. Whether the test passed or not.
        attempt: Text of the attempt.

        Note: Even if dry, will still physically call get_problem_problemid,
        which may mutate the DB.
        """
        problemid = self.get_problem_problemid(exercisename)

        return self.insert({
                'problemid': problemid,
                'loginid': user.id,
                'date': date,
                'complete': complete,
                'attempt': attempt,
            }, 'problem_attempt',
            frozenset(['problemid','loginid','date','complete','attempt']),
            dry=dry)

    def write_problem_save(self, user, exercisename, date, text, dry=False):
        """Writes text to the problem_save table (for when the user saves an
        exercise). Creates a new row, or overwrites an existing one if the
        user has already saved that problem.
        (Unlike problem_attempt, does not keep historical records).
        """
        problemid = self.get_problem_problemid(exercisename)

        try:
            return self.insert({
                    'problemid': problemid,
                    'loginid': user.id,
                    'date': date,
                    'text': text,
                }, 'problem_save',
                frozenset(['problemid','loginid','date','text']),
                dry=dry)
        except pg.ProgrammingError:
            # May have failed because this problemid/loginid row already
            # exists (they have a unique key constraint).
            # Do an update instead.
            if dry:
                # Shouldn't try again, must have failed for some other reason
                raise
            self.update({
                    'problemid': problemid,
                    'loginid': user.id,
                },
                {
                    'date': date,
                    'text': text,
                }, "problem_save",
                frozenset(['date', 'text']),
                frozenset(['problemid', 'loginid']))

    # SUBJECTS AND ENROLEMENT

    def get_offering_semesters(self, subjectid, dry=False):
        """
        Get the semester information for a subject as well as providing 
        information about if the subject is active and which semester it is in.
        """
        query = """\
SELECT offeringid, subj_name, year, semester, active
FROM semester, offering, subject
WHERE offering.semesterid = semester.semesterid AND
    offering.subject = subject.subjectid AND
    offering.subject = %d;"""%subjectid
        if dry:
            return query
        results = self.db.query(query).dictresult()
        # Parse boolean varibles
        for result in results:
            result['active'] = _parse_boolean(result['active'])
        return results

    def get_offering_members(self, offeringid, dry=False):
        """
        Gets the logins of all the people enroled in an offering
        """
        query = """\
SELECT login.login AS login, login.fullname AS fullname
FROM login, enrolment
WHERE login.loginid = enrolment.loginid AND
    enrolment.offeringid = %d
    ORDER BY login.login;"""%offeringid
        if dry:
            return query
        return self.db.query(query).dictresult()


    def get_enrolment_groups(self, login, offeringid, dry=False):
        """
        Get all groups the user is member of in the given offering.
        Returns a list of dicts (all values strings), with the keys:
        name, nick
        """
        query = """\
SELECT project_group.groupnm as name, project_group.nick as nick
FROM project_set, project_group, group_member, login
WHERE login.login=%s
  AND project_set.offeringid=%s
  AND group_member.loginid=login.loginid
  AND project_group.groupid=group_member.groupid
  AND project_group.projectsetid=project_set.projectsetid
""" % (_escape(login), _escape(offeringid))
        if dry:
            return query
        return self.db.query(query).dictresult()

    # PROJECT GROUPS

    def get_offering_info(self, projectsetid, dry=False):
        """Takes information from projectset and returns useful information 
        about the subject and semester. Returns as a dictionary.
        """
        query = """\
SELECT subjectid, subj_code, subj_name, subj_short_name, url, year, semester, 
active
FROM subject, offering, semester, project_set
WHERE offering.subject = subject.subjectid AND
    offering.semesterid = semester.semesterid AND
    project_set.offeringid = offering.offeringid AND
    project_set.projectsetid = %d;"""%projectsetid
        if dry:
            return query
        return self.db.query(query).dictresult()[0]

    def get_projectgroup_members(self, groupid, dry=False):
        """Returns the logins of all students in a project group
        """
        query = """\
SELECT login.login as login, login.fullname as fullname
FROM login, group_member
WHERE login.loginid = group_member.loginid AND
    group_member.groupid = %d
ORDER BY login.login;"""%groupid
        if dry:
            return query
        return self.db.query(query).dictresult()

    def get_groups_by_projectset(self, projectsetid, dry=False):
        """Returns all the groups that are in a particular projectset"""
        query = """\
SELECT groupid, groupnm, nick, createdby, epoch
FROM project_group
WHERE project_group.projectsetid = %d;"""%projectsetid
        if dry:
            return query
        return self.db.query(query).dictresult()

    def close(self):
        """Close the DB connection. Do not call any other functions after
        this. (The behaviour of doing so is undefined).
        """
        self.db.close()
        self.open = False
