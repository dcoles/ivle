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

While installing from a distribution package is often a better idea for
users, developers will need to install from a plain source tree.

To get the tree, either grab and extract a release tarball, or get the
very latest code using bzr: ::

   bzr get lp:ivle

You should then change into the new source directory.

As IVLE needs to compile some binaries, you must first build, then
install it: ::

   ./setup.py build
   sudo ./setup.py install

Unlike the package, you will have to manually set up the database and
configuration.

.. TODO: Separate IVLE PostgreSQL account.

First you must create a PostgreSQL database, and populate it with the
IVLE schema. You may use any name for the database. ::

   sudo -u postgres createdb ivle
   sudo -u postgres createlang plpgsql ivle
   sudo -u postgres psql -d ivle < userdb/users.sql

The configuration wizard - ``ivle-config`` - will ask you a series of
questions. Apart from database settings, the defaults should be correct
for a development system. If deploying IVLE properly - particularly on
multiple nodes - several options will need to be changed. Watching
carefully, run: ::

   sudo ivle-config


Basic configuration
===================

.. Note: Place here only the configuration required to get the system
   installed and running. Any further configuration should go in config.rst.

IVLE needs a directory hierarchy in which to store filesystem data, which
by default lives in ``/var/lib/ivle``. Create it now. ::

   sudo ivle-createdatadirs

.. TODO: Setting jail/devmode, jail/suite, jail/extra_packages...
         We also need to document setting of the default mirror, once
         issue #150 is fixed.

You will require a self-contained jail environment in which to safely
execute student code. The creation process basically downloads a minimal
Ubuntu system and installs it in ``/var/lib/ivle/jails/__base__``. Note
that this could download a couple of hundred megabytes. You should
replace the URL with a good close Ubuntu mirror. ::

   sudo ivle-buildjail -r -m http://url.to.archive/mirror

Configuring Apache
------------------

IVLE makes use of two Apache virtual hosts: one for the application itself,
and one for the Subversion services. There are example configuration files
in ``examples/config/apache.conf`` and ``examples/config/apache-svn.conf``,
which will run IVLE at ``http://ivle.localhost/``.

On a Debian or Ubuntu system, just copy those two files into
``/etc/apache2/sites-available`` under appropriate names (eg. ``ivle`` and
``ivle-svn``). Then you need to activate them: ::

   sudo a2ensite ivle
   sudo a2ensite ivle-svn
   sudo /etc/init.d/apache2 reload


.. note::
   For more advanced configuration, see :ref:`Configuring IVLE
   <ref-configuring-ivle>`.
