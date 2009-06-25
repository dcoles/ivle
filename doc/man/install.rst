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

************
Installation
************

System requirements
===================

Given versions are those on which IVLE is known to work; earlier versions
might work too. Debian/Ubuntu package names are given after the name of the
software.

* Ubuntu 8.04 or later (other distros should work with some tweaking, but are untested)
* Apache 2.x with modules:
   + mod_python (``libapache2-mod-python``)
   + mod_dav_svn and mod_authz_svn (``libapache2-svn``)
* Python 2.5 or 2.6 with modules:
   + pysvn (``python-svn``)
   + cjson (``python-cjson``)
   + Genshi (``python-genshi``)
   + ConfigObj (``python-configobj``)
   + Routes (``python-routes``)
   + docutils (``python-docutils``)
   + epydoc (``python-epydoc``)
   + Storm (``python-storm``)
   + psycopg2 (``python-psycopg2``)
* jQuery (``libjs-jquery``)
* PostgreSQL 8.3 or later (``postgresql``)
* Subversion (``subversion``)
* debootstrap (``debootstrap``)
* GCC and related build machinery (``build-essential``)

Master versus slave servers
===========================

Installing from a Debian package
================================

Installing from source
======================

Basic configuration
===================

.. Note: Place here only the configuration required to get the system
   installed and running. Any further configuration should go in config.rst.

.. note::
   For more advanced configuration, see :ref:`Configuring IVLE
   <ref-configuring-ivle>`.
