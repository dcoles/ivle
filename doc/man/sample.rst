.. IVLE - Informatics Virtual Learning Environment
   Copyright (C) 2007-2009 The University of Melbourne

.. This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

.. This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

.. You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

***********
Sample data
***********

IVLE comes with supplied sample data to give a quick overview of the system.
This sample data may be installed by an administrative script. It should not
be installed in a production environment.

The sample data consists of database entries, for populating sample subjects,
offerings, users, projects, groups and worksheets, as well as some sample
files in users' Subversion repositories.

Installing the sample data
==========================

The data is stored in an SQL dump file, in ``examples/db/sample.sql``.

You must import this data into a **fresh** IVLE database. You can
re-initialise your database by running ``sudo -u postgres dropdb ivle``, and
then following the database setup instructions, in the section
:ref:`database-setup`.

The data may be imported by running the following command::

    sudo -u postgres psql ivle < examples/db/sample.sql

.. XXX
.. warning:: Instructions on fixing up the user's repositories and file
   systems to come.

What is included
================

Subjects, semesters and offerings
---------------------------------

There are four semesters in the database: 2009 semesters 1 and 2, and 2010
semesters 1 and 2.

.. note:: We pretend that we are in 2009 semester 2 (even if that doesn't
   agree with the system clock). Therefore, 2009 semester 1 is a "past
   semester", 2009 semester 2 is the "current semester", and the 2010
   semesters are "future semesters."

There are four subjects in the database, with subject short names ivle-101,
ivle-102, ivle-201 and ivle-202.

The subjects have offerings for some of the semesters, as shown in this table:

+------+----------+-----------+
| Year | Semester | Subject   |
+======+==========+===========+
| 2009 | 1        | ivle-101  |
+------+----------+-----------+
| 2009 | 2        | ivle-102  |
+------+----------+-----------+
| 2010 | 1        | ivle-101  |
+------+----------+-----------+
| 2010 | 1        | ivle-201  |
+------+----------+-----------+
| 2010 | 2        | ivle-102  |
+------+----------+-----------+
| 2010 | 2        | ivle-202  |
+------+----------+-----------+

Users
-----

There are four users (username/password). Note that in all cases, the password
is "password".

* admin/password: This user has administrative rights over the entire system.
* lecturer/password: This is a normal user, but is enrolled as a lecturer in
  100101 (2009 semester 1) and 100102 (2009 semester 2).
* studenta/password: This is a normal user, enrolled in 100101 (2009 semester
  1) and 100102 (2009 semester 2).
* studentb/password: This is a normal user, enrolled in 100102 (2009 semester
  2). This student has not yet accepted the Terms of Service, so does not have
  a jail created, etc.

.. note:: For the first three users, the Subversion password is also
   "password". This means it is possible to access their SVN repository
   with a stand-alone SVN client with that password. This is somewhat
   unrealistic, as the SVN password in IVLE is usually a randomly-generated
   string, not related to the user's IVLE login password.

   When studentb logs in for the first time, his SVN repository is created,
   and given a random password.

Updating the sample data
========================

For developers: If you need to update the sample data, follow this procedure.

Run the following command::

    pg_dump --schema=public --disable-triggers --data-only --column-inserts \
        --inserts --no-owner ivle > examples/db/sample.sql

Then check the diff. You may hand-edit the SQL file, but only for the purpose
of fixing up unsightly data -- it should be possible to reload from the script
and re-export with no diff.
