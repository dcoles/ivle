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

*********************
Architecture overview
*********************

This page describes the various subsystems of IVLE.

.. image:: /images/ivle-system-diagram.png

The IVLE web application
========================

User management server
======================

The "user management" server (:file:`usrmgt-server`) is an
inappropriately-named program which must be run as root in the background of
an IVLE instance. It is responsible for performing tasks at the request of the
IVLE web application, which require root privileges:

* Activating users when they first log into the system (including the creation
  of jails and user Subversion repositories).
* Creating group Subversion repositories.
* Rebuilding Subversion configuration files.

Subversion server
=================

User jails
==========

Scripts
=======

Database
========

Authentication
==============

There are two mechanisms by which IVLE can connect to an external server to
get information about users. These are typically used to connect to an
institution's central database to authenticate students, and download student
details (such as names and subject enrolment details).

Neither of these mechanisms are necessary; they are only useful where
third-party authentication is required.

.. _ref-auth-modules:

Auth modules
------------

IVLE's database contains user accounts, which includes a password (hash)
field. In this way, IVLE is fully-functioning without third-party
authentication modules. However, it is also often desirable to allow users to
log in without storing their password hash in the local database. IVLE allows
plug-in "auth modules" which can authenticate users with arbitrary logic, and
also create new user accounts.

This has at least the following two use cases:

* Allowing users to authenticate upon each login with a remote server. This
  allows users to log in without ever storing their password hash locally.
* Allowing users who have never used IVLE to log in, without an IVLE user
  account. Upon seeing an unknown username, an auth module can connect to a
  remote server, authenticate the unknown user, and create an IVLE user
  account on-the-fly, optionally downloading additional details (such as full
  name).

TODO: Describe how auth modules work.

.. _ref-subject-pulldown-modules:

Subject pulldown modules
------------------------

IVLE maintains lists of enrolled students in each subject, providing access to
worksheets and allowing submissions for enrolled users. Again, enrolments can
be made manually, but IVLE also allows plug-in "subject pulldown modules"
which can enrol students with arbitrary logic.

This allows a third-party server to dictate which IVLE users are enrolled in
which IVLE subjects.

Subject pulldown modules are used by the :program:`ivle-enrolallusers` script
to automatically enrol all existing users in subjects. Note that this does not
enrol users who are not in the IVLE database (perhaps because a third-party
auth module is being used to create user accounts on-the-fly, and some
students have not yet logged in for the first time).

Because of this, subject pulldown modules are also used whenever a student
logs in. This ensures that students who log in for the first time are
automatically enrolled in all subjects, according to the third-party server,
and also ensures that enrolments are kept up-to-date, should the third-party
server add new enrolments, or should new subjects be created in IVLE.

.. note::
   Enrolments are never removed by subject pulldown modules, only added.
   Students can only be un-enrolled from a subject by an administrator.

TODO: Describe how subject pulldown modules work.
