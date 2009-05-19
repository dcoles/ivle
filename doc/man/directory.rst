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

**************************
System directory hierarchy
**************************

IVLE is a complicated piece of software, and installs several components into
various places in your filesystem. This page details exactly where the
components will be installed, and what their purpose is:

* The IVLE code itself
    * The main web application, as a Python package
    * Numerous Python scripts (:file:`ivle-*`), in your :envvar:`PATH`
    * Several services (binary files and Python code)
* The configuration files
* The jails
* The subversion repositories
    * The subversion configuration files

.. XXX Copy the contents of Planning/Directory_hierarchy from our dev wiki.

The IVLE codebase
=================

Configuration files
===================

User jails
==========

Subversion repositories and configuration
=========================================
