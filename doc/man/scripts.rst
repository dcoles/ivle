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

*************
Admin scripts
*************

IVLE has a number of Admin scripts to configure IVLE or for functionality not  
directly in the web application.

Most of these script are required to be run as root.

ivle-addexercise
----------------

.. program:: ivle-addexercise

:program:`ivle-addexercise <EXERCISE>`

Adds an XML encoded exercise to the IVLE database.

.. cmdoption:: <EXERCISE>

    The XML file containing the exercise to be uploaded.

ivle-adduser
------------

.. program:: ivle-adduser

:program:`ivle-adduser [OPTIONS] <LOGIN> <FULLNAME>`

Script to create a new user.

.. FIXME: "This can also be done through the administration interface."
    (Not yet!)

This script wraps common.makeuser. It also creates a unix account which 
common.makeuser does not. (This script may not be appropriate for production 
on a multi-node environment)

.. cmdoption:: <LOGIN>

    The login name of the new user

.. cmdoption:: <FULLNAME>

    The full name of the user

.. cmdoption:: -p <PASSWORD>, --password <PASSWORD>

    Cleartext password

.. cmdoption:: -n <NICK>, --nick <NICK>

    Display name (defaults to <FULLNAME>)

.. cmdoption:: -e <EMAIL>, --email <EMAIL>

    Email address

.. cmdoption:: -s <SID>, --studentid <SID>

    Student ID

.. cmdoption:: --admin

    Give the user full administrative privileges


ivle-buildjail
--------------

.. program:: ivle-buildjail

:program:`ivle-buildjail [OPTIONS]`

.. cmdoption:: -r, --recreate

    Completely recreate the jail - don't just update its IVLE code.

    .. warning::

        This may download hundreds of megabytes from the location specified by 
        ``<MIRROR>``.

.. cmdoption:: -u, --upgrade

    Apply any package updates in the jail.

.. cmdoption:: -m <MIRROR>, --mirror <MIRROR>

    Sets the APT mirror.


ivle-cloneworksheets
--------------------

.. program:: ivle-cloneworksheets

:program:`ivle-cloneworksheets <OLDSUBJECTCODE> <OLDYEAR> <OLDSEMESTER> 
<NEWSUBJECTCODE> <NEWYEAR> <NEWSEMESTER>`

Populates the subject specified by ``<NEWSUBJECTCODE> <NEWYEAR> 
<NEWSEMESTER>`` with a copy of the worksheets from the subject specified by 
``<OLDSUBJECTCODE> <OLDYEAR> <OLDSEMESTER>``.


ivle-config
-----------

.. program:: ivle-config

:program:`ivle-config [ARG1] [ARG2] ...`

Configures IVLE with machine-specific details, most notably, various paths.
Either prompts the administrator for these details or accepts them as
command-line args.

Command-line arguments may be any of the :ref:`configuration option 
<ref-configuration-options>` used in :file:`ivle.conf`. They are provided in 
the form of :samp:`--{section}/{subsection}/{property} {VALUE}` such as 
``--urls/root ivle.org`` or ``--media/externals/jquery 
/usr/share/javascript/jquery``.

Automatically creates the file :file:`/etc/ivle.conf`.


ivle-createdatadirs
-------------------

.. program:: ivle-createdatadirs

:program:`ivle-createdatadirs`

Creates an IVLE data hierarchy if it does not already exist.


ivle-enrol
----------

.. program:: ivle-enrol

:program:`ivle-enrol <LOGIN> <SUBJECTCODE> <YEAR> <SEMESTER> [ROLE]`

Script to enrol a user in an offering.

.. cmdoption:: <LOGIN>

    The login of the user to enrol.

.. cmdoption:: <SUBJECTCODE>

    The subject code of the offering.

.. cmdoption:: <YEAR>

    The year of the offering.

.. cmdoption:: <SEMESTER>

    The semester of the offering

.. cmdoption:: [ROLE]

    Set the role of the user. Should be one of 'student' (default), 'tutor' or 
    'lecturer'.


ivle-enrolallusers
------------------

.. program:: ivle-enrolallusers

:program:`ivle-enrolallusers`

Script to add enrolments for all users on the system.
Pulls from the configured :ref:`subject pulldown module 
<ref-subject-pulldown-modules>` the subjects each student
is enrolled in, and adds enrolments to the database.
Does not remove any enrolments.

Requires root to run.

.. cmdoption:: -u <LOGIN>, --user <LOGIN>

    Just perform enrolment for user ``<LOGIN>``

.. cmdoption:: -v, --verbose

    Print out the details of each enrolment.

.. cmdoption:: -y, --year

    If specified, year to make enrolments for (default is the current year)


ivle-fetchsubmissions
---------------------

.. program:: ivle-fetchsubmissions

:program:`ivle-fetchsubmissions [OPTIONS] <SUBJECT> <PROJECTNAME>`

Retrieves all submissions for a given project. Places each submission in its 
own directory, in a subdirectory of '.'. Any errors are reported to stderr 
(otherwise is silent).

Requires root to run.

.. cmdoption:: <SUBJECT>

    The short name given to the subject

.. cmdoption:: <PROJECTNAME>

    The name of the project to retrieve.

.. cmdoption:: -s <SEMESTER>, --semester <SEMESTER>

    Semester of the subject's offering (eg. 2009/1). Defaults to the currently 
    active semester.

.. cmdoption:: -d <PATH>, --dest <PATH>

    Destination directory (defaults to '.') to place submissions. Will create 
    subdirectories in this directory of the form 
    ``subject/year/semester/project``.

.. cmdoption:: -z, --zip

    Store each submission in a Zip file.

.. cmdoption:: -v, --verbose

    Print out the name of each submission as it is extracted.

.. cmdoption:: --no-txt

    Disable writing a text file with metadata about each submission.


ivle-listusers
--------------

.. program:: ivle-listusers

:program:`ivle-listusers [OPTIONS]`

Gets a list of all users in the IVLE database.

Requires root to run.

.. cmdoption:: -n, --names

    Only prints the logins of users


ivle-marks
----------

.. program:: ivle-marks

:program:`ivle-marks [OPTIONS] <SUBJECT>`

Reports each student's marks for a given subject offering.

Requires root to run.

.. cmdoption:: <SUBJECT>

    The short name given to the subject

.. cmdoption:: -s <SEMESTER>, --semester <SEMESTER>

    Semester of the subject's offering (eg. 2009/1). Defaults to the currently 
    active semester.

.. cmdoption:: -c <CUTOFF>, --cutoff <CUTOFF>

    Cutoff date (calculate the marks as of this date). Should be provided in 
    the form of ``YYYY-MM-DD H:M:S``.


ivle-mountallusers
------------------

.. program:: ivle-mountallusers

:program:`ivle-mountallusers`

Attempts to mount the jails of all users.

.. note::

    Administrators should not be required to manually run this script for 
    regular operation.  IVLE will automatically mount user's jails on demand.

Requires root to run.

.. cmdoption:: -v, --verbose

    Prints the details of each user's jail being mounted/unmounted

.. cmdoption:: -u, --unmount

    Unmount jails instead of mounting them.


ivle-refreshfilesystem
----------------------

.. program:: ivle-refreshfilesystem

:program:`ivle-refreshfilesystem`

Refresh parts of the filesystem that are generated from the database.

In particular, the Subversion authorisation files are rewritten.


ivle-remakeuser
---------------

.. program:: ivle-remakeuser

:program:`ivle-remakeuser [OPTIONS] <USER>`

:program:`ivle-remakeuser [OPTIONS] -a`

Rebuilds the Jail of a user or all users in IVLE. This will not delete the 
data of the users being rebuilt.

Requires root to run.

.. cmdoption:: <USER>

    Login of the user whose Jail will be rebuilt.

.. cmdoption:: -v, --verbose

    Prints the details of each user's jail being remade.

.. cmdoption:: -a, --all

    Rebuild all users Jails.


ivle-showenrolment
------------------

.. program:: ivle-showenrolment

:program:`ivle-showenrolment <USER>`

Shows the enrolments of a user. Prints subject code, subject name, year, 
semester and role the user has in each subject they are enrolled in.

Requires root to run.

.. cmdoption:: <USER>

    Login of the user to view enrolments details.
