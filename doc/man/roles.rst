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

.. _ref-user-roles:

**********
User roles
**********

IVLE users can be given roles, giving them additional power in the system. The
roles are centered around a typical university teaching structure, with
tutors, lecturers and system administrators.

This page lists precisely what is permitted by each role.

Note that the roles are hierarchical. Being a member of a role implies all of
the powers of lesser roles.

Most roles are *per-offering*, which means the user only has the powers of
that role when dealing with a specific offering of a subject. (For example, a
lecturer of subject "ivle-101" for 2009 semester 1 is just an ordinary user
with respect to any other subject, or any other offering of "ivle-101").

Ordinary users
--------------

This is the default role for any user. Note that we do not refer to "ordinary
users" as "students", because "student" implies an enrolment in a particular
offering.

All users have the ability to:

* Store and edit files in the file system,
* Execute Python code in the Python console,
* Serve files privately and publicly,
* View and edit some of their own details (e.g., can edit display name, but
  not full name, which is required to be the user's formal name).

Students
--------

The role of "student" is offering-specific. Any user enrolled in an offering
is a "student" in that offering.

In addition to the abilities of ordinary users, students have the ability to:

* View the "subject page" for the offering,
* View any worksheet in the offering, and its exercises,
* Submit attempts at any exercise in any worksheet in the offering,
* Receive a mark for worksheet completion in the offering,
* Submit a solo project for the offering,
* Submit a group project for the offering, on behalf of any group they are in.

Tutors
------

The role of "tutor" is offering-specific. Users may be enrolled in an offering
as "tutor" by a lecturer or admin.

In addition to the abilities of students, tutors have the ability to:

* View submissions to projects in the offering,
* Check out (with an external Subversion client) the part of a student or
  group's Subversion repository which was submitted to a project in the
  offering,
* Enrol a user in the offering as a student, if the system administrator has
  allowed it (see ``tutors_can_enrol_students`` under
  :ref:`policy configuration <ref-configuration-policy>`). This is
  **disabled** by default,
* Create and edit worksheets for the offering, if the system administrator has
  allowed it (see ``tutors_can_edit_worksheets`` under
  :ref:`policy configuration <ref-configuration-policy>`). This is **enabled**
  by default,
* Create and edit exercises *for any offering* (as exercises are not
  offering-specific), if the system administrator has allowed it (see
  ``tutors_can_edit_worksheets`` under :ref:`policy configuration
  <ref-configuration-policy>`). This is **enabled** by default.

Lecturers
---------

The role of "lecturer" is offering-specific. Users may be enrolled in an
offering as "lecturer" by an admin.

In addition to the abilities of tutors, lecturers have the ability to:

* Enrol a user in the offering, as a student or tutor,
* Create and edit worksheets for the offering
* Create and edit exercises *for any offering* (as exercises are not
  offering-specific),
* Edit the details of the offering (such as description and URL),
* Create and edit projects and project sets for the offering,
* Create project groups, and add/remove students from them.

Admins
------

The ultimate role is "admin". This is a site-wide role (it is not specific to
any offering).

Admins have the ability to:

* Do anything a lecturer can do in any offering,
* See stack traces when IVLE generates an internal server error (normal users
  see a generic error page),
* See a list of all users in the system,
* View and edit all details for all users, including "fixed" fields such as
  full name, and change any user's password without knowing the old one,
* Enrol a user as a lecturer in any offering,
* Upgrade any user to admin status, or revoke admin status,
* Disable (ban) any user from accessing the system at all, or enable a user,
* See a list of all subjects and offerings in the system,
* Create new subjects and offerings,
* Edit the details of any subject (nb: not just an offering),
* Create new semesters,
* Change which subject/semester an offering is bound to.
