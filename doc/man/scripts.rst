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

.. _ref-admin-scripts:

*************
Admin scripts
*************

IVLE has a number of admin scripts for uncommon configuration or other
functionality not available in the web application.

Most of these scripts must be run as root.

ivle-addexercise
----------------

.. program:: ivle-addexercise

:program:`ivle-addexercise <EXERCISE>`

Adds an XML encoded exercise to the IVLE database. This is primarily
for importing exercises that pre-date the database storage system.

The exercise's name will be set to the complete path specified on the
command line -- keep this in mind when choosing a working directory.

.. cmdoption:: <EXERCISE>

    The XML file containing the exercise to be uploaded.

ivle-adduser
------------

.. program:: ivle-adduser

:program:`ivle-adduser [OPTIONS] <LOGIN> <FULLNAME>`

Creates a new user in the database. On-disk structures (jails and
Subversion repositories) will be created upon first login.

.. FIXME: "This can also be done through the administration interface."
    (Not yet!)


.. cmdoption:: <LOGIN>

    Login name of the new user

.. cmdoption:: <FULLNAME>

    Full name of the user

.. cmdoption:: -p <PASSWORD>, --password <PASSWORD>

    Cleartext password. If omitted, external authentication mechanisms
    will be tried.

.. cmdoption:: -n <NICK>, --nick <NICK>

    Display name (defaults to <FULLNAME>)

.. cmdoption:: -e <EMAIL>, --email <EMAIL>

    Email address

.. cmdoption:: -s <SID>, --studentid <SID>

    Student ID

.. cmdoption:: --admin

    Give the user global IVLE administrative privileges


ivle-buildjail
--------------

.. program:: ivle-buildjail

:program:`ivle-buildjail [OPTIONS]`

Creates or updates the IVLE jail template. 

.. cmdoption:: -r, --recreate

    Completely recreate the jail - don't just update its IVLE code.

    .. warning::

        This may download hundreds of megabytes from the location specified by 
        ``<MIRROR>``.

.. cmdoption:: -u, --upgrade

    Apply any package updates in the jail.

.. cmdoption:: -m <MIRROR>, --mirror <MIRROR>

    Sets the APT mirror. May also be specified in the ``jail/mirror``
    config key.


ivle-cloneworksheets
--------------------

.. program:: ivle-cloneworksheets

:program:`ivle-cloneworksheets <OLDSUBJECTCODE> <OLDYEAR> <OLDSEMESTER> 
<NEWSUBJECTCODE> <NEWYEAR> <NEWSEMESTER>`

Populates the offering specified by ``<NEWSUBJECTCODE> <NEWYEAR> 
<NEWSEMESTER>`` with a copy of the worksheets from the offering specified by 
``<OLDSUBJECTCODE> <OLDYEAR> <OLDSEMESTER>``.

.. note::
    Admins may also clone worksheets from the offering administration panel
    in the web interface.


ivle-config
-----------

.. program:: ivle-config

:program:`ivle-config [ARG1] [ARG2] ...`

Configures IVLE with machine-specific details, most notably various paths.
Either prompts the administrator for these details or accepts them as
command line arguments.

Command line arguments may be any of the :ref:`configuration option 
<ref-configuration-options>` used in :file:`ivle.conf`. They are provided in 
the form of :samp:`--{section}/{subsection}/{property} {VALUE}` such as 
``--urls/root ivle.org`` or ``--media/externals/jquery 
/usr/share/javascript/jquery``.

Creates or updates :file:`/etc/ivle/ivle.conf` with the selected values,
and overwrites :file:`/etc/ivle/plugins.d/000default` with the latest
default plugin list.


ivle-createdatadirs
-------------------

.. program:: ivle-createdatadirs

:program:`ivle-createdatadirs`

Creates the IVLE data hierarchy (by default under :file:`/var/lib/ivle`) if
it does not already exist.


ivle-enrol
----------

.. program:: ivle-enrol

:program:`ivle-enrol <LOGIN> <SUBJECTCODE> <YEAR> <SEMESTER> [ROLE]`

Enrols a user in an offering.

.. note::
    Users may also be enrolled from the offering administration panel
    in the web interface.

.. cmdoption:: <LOGIN>

    Login of the user to enrol

.. cmdoption:: <SUBJECTCODE>

    Subject code

.. cmdoption:: <YEAR>

    Offering year

.. cmdoption:: <SEMESTER>

    Offering semester

.. cmdoption:: [ROLE]

    Role of the user. Should be one of 'student' (default), 'tutor' or
    'lecturer'.


ivle-enrolallusers
------------------

.. program:: ivle-enrolallusers

:program:`ivle-enrolallusers`

Adds enrolments for all users on the system.
Pulls from the configured :ref:`subject pulldown module 
<ref-subject-pulldown-modules>` the subjects each student
is enrolled in, and adds enrolments to the database.
Does not remove any enrolments.

.. note::
    Pulldown modules are consulted for each user each time they log in,
    so use of this script may not be required.

.. cmdoption:: -u <LOGIN>, --user <LOGIN>

    Just perform enrolment for user ``<LOGIN>``

.. cmdoption:: -v, --verbose

    Print out the details of each enrolment.


ivle-fetchsubmissions
---------------------

.. program:: ivle-fetchsubmissions

:program:`ivle-fetchsubmissions [OPTIONS] <SUBJECT> <PROJECT>`

Retrieves all submissions for a given project. Places each submission in its 
own subdirectory of the current directory. Any errors are reported to stderr
(otherwise is silent).

.. note::
    Since this script accesses Subversion repositories through the
    filesystem, it must be run on the master server.

.. cmdoption:: <SUBJECT>

    Subject short (URL) name

.. cmdoption:: <PROJECTNAME>

    Project short (URL) name

.. cmdoption:: -s <SEMESTER>, --semester <SEMESTER>

    Semester of the offering (eg. 2009/1). Defaults to the currently
    active semester.

.. cmdoption:: -d <PATH>, --dest <PATH>

    Destination directory (defaults to the current directory) in
    which to place submissions. Will create subdirectories in this
    directory of the form ``subject/year/semester/project``.

.. cmdoption:: -z, --zip

    Store each submission in a Zip file.

.. cmdoption:: -v, --verbose

    Print the name of each submission as it is extracted.

.. cmdoption:: --no-txt

    Disable writing a text file with metadata about each submission.


ivle-listusers
--------------

.. program:: ivle-listusers

:program:`ivle-listusers [OPTIONS]`

Lists all users in the IVLE database.

.. note::
    Users may also be listed and administered through the web interface,
    from the *Users* item in the IVLE menu.

.. cmdoption:: -n, --names

    Print only each user's login name


ivle-mountallusers
------------------

.. program:: ivle-mountallusers

:program:`ivle-mountallusers`

Attempts to mount the jails of all users.

.. note::

    Administrators should not need to manually run this script for regular
    operation.  IVLE will automatically mount users' jails on demand.

.. cmdoption:: -v, --verbose

    Print a message for each mount or unmount.

.. cmdoption:: -u, --unmount

    Unmount jails instead of mounting them.


ivle-refreshfilesystem
----------------------

.. program:: ivle-refreshfilesystem

:program:`ivle-refreshfilesystem`

Refresh parts of the filesystem to match the database.

In particular:
 - all jails are rebuilt
 - missing user jails are created
 - missing user and group Subversion repositories are created
 - jails for missing users are removed
 - Subversion repositories for missing users or groups are removed
 - the Subversion password file is updated
 - the Subversion authorisation files are rewritten

.. warning::
    Due to the full jail rebuilds, existing jail mounts may be broken
    after this script has run. To recover from this situation, use
    ``ivle-mountallusers`` to unmount all of the jails.

.. note::
    Jails and Subversion repositories are not entirely removed. They
    can be found in a timestamped directory alongside their parent.


ivle-remakeuser
---------------

.. program:: ivle-remakeuser

:program:`ivle-remakeuser [OPTIONS] <USER>`

:program:`ivle-remakeuser [OPTIONS] -a`

Rebuilds the jail of a single user or of all users in IVLE. This will
retain all user data, but recreate the rest of the hierarchy and
internal configuration files.

.. cmdoption:: <USER>

    Login of the user whose jail should be rebuilt

.. cmdoption:: -a, --all

    Rebuild the jail of every user

.. cmdoption:: -v, --verbose

    Print a message as each user's jail is remade


ivle-showenrolment
------------------

.. program:: ivle-showenrolment

:program:`ivle-showenrolment <USER>`

Shows the enrolments of a user. Prints subject code, subject name, year, 
semester and the held role for each subject in which they are enrolled.

.. cmdoption:: <USER>

    Login of the user
