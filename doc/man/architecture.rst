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
