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

.. _sample-data:

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

You must import this data into a **fresh** IVLE database. If you already have
a working IVLE install, it will have to be erased. A script is provided
which performs the following tasks:

* Unmounts all users with accounts in the current database,
* Drops the IVLE database if it already exists (prompting first),
* Creates and initialises a new IVLE database, as per :ref:`database-setup`,
* Populates the database with the sample data,
* Creates data directories and subversion repositories for all users, backing
  up directories for any existing users.

The script is executed with the following command::

    sudo ivle-loadsampledata examples/db/sample.sql

.. warning:: This script essentially destroys all contents in an existing IVLE
   installation. Be sure you wish to do this.

.. note:: The script may fail at the "dropping database" phase if Apache or
   another process are using the database. It is best to stop Apache before
   executing the script.

   If the database exists, but is not properly initialised, then the script
   may fail. In this case, you should manually run ``ivle-mountallusers -u``,
   then drop the database, to ensure a clean build.

   If there are any existing users (including sample users from previous runs
   of the script), their files and subversion repos will be moved out of the
   way to a backup location, ``/var/lib/ivle/jails-removed-<date>/``.
   If you run this script regularly, your ``/var/lib/ivle/`` will become full
   of these backups, so you may wish to remove them often. However, they are
   typically fairly small (a few hundred kilobytes each), because they only
   contain user content, not the full jail image.

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

There are five users (username/password). Note that in all cases, the password
is "password".

* admin/password: This user has administrative rights over the entire system.
* lecturer/password: This is a normal user, but is enrolled as a lecturer in
  100101 (2009 semester 1) and 100102 (2009 semester 2).
* tutor/password: This is a normal user, but is enrolled as a tutor in
  100102 (2009 semester 2).
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

Files
-----

The repository for user "studenta" has a few sample files. All of the
directories must be checked out (using the Checkout button) before the files
can be seen from the IVLE application.

* In the :file:`stuff` directory is a sample file, :file:`hello.py`. This is a
  simple Python script, which can be executed with the "Serve" command.

Projects
--------

The subject 100102 has two project sets and three projects. This demonstrates
the relationship between project sets and projects.

The first project set is a solo project set (every student works by
themselves on all projects). It has one project in it.

The second project set is a group project set, for groups of 3. That means
students work in the *same* group of 3 for every project in the set. It has
two projects in it, demonstrating that the students get to keep their group
(including all of the group files) across the two projects in this set.

Finally, there is a single group for projects 2 and 3, which has the students
studenta and studentb enlisted.

Worksheets
----------

There are not yet any worksheets.

Exercises
---------

There is currently a single exercise, ``factorial``, which prompts the user to
write a factorial function and tests its correctness.

Updating the sample data
========================

For developers: If you need to update the sample data, follow this procedure.

Run the following command::

    pg_dump --schema=public --disable-triggers --data-only --column-inserts \
        --inserts --no-owner ivle > examples/db/sample.sql

Then check the diff. You may hand-edit the SQL file, but only for the purpose
of fixing up unsightly data -- it should be possible to reload from the script
and re-export with no diff.
