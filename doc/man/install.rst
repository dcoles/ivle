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

.. _ref-install:

************
Installation
************

System requirements
===================

Given versions are those on which IVLE is known to work; earlier versions
might work too. Debian/Ubuntu package names are given after the name of the
software.

.. If this list changes, you also need to change the list below.

* Ubuntu 8.04 or later (other distros should work with some tweaking, but are untested)
* Apache 2.x (``apache2``) with modules:
   + mod_python (``libapache2-mod-python``)
   + mod_dav_svn and mod_authz_svn (``libapache2-svn``)
* Python 2.5 (``python2.5``) or 2.6 (``python2.6``) with modules:
   + cjson (``python-cjson``)
   + ConfigObj (``python-configobj``)
   + docutils (``python-docutils``)
   + epydoc (``python-epydoc``)
   + FormEncode (``python-formencode``)
   + Genshi (``python-genshi``)
   + psycopg2 (``python-psycopg2``)
   + pysvn (``python-svn``)
   + Routes (``python-routes``)
   + Storm (``python-storm``)
* jQuery (``libjs-jquery``)
* PostgreSQL 8.3 or later (``postgresql``)
* Subversion (``subversion``)
* debootstrap (``debootstrap``)
* rsync (``rsync``)
* GCC and related build machinery (``build-essential``)

Master versus slave servers
===========================

Installing from a Debian package
================================

Installing from source
======================

.. If this list changes, you also need to change the list above.

If you want to grab all of the required packages in one command, use::

    sudo apt-get install apache2 libapache2-mod-python libapache2-svn \
    python2.6 python-cjson python-configobj python-docutils python-epydoc \
    python-formencode python-genshi python-psycopg2 python-svn python-routes \
    python-storm libjs-jquery postgresql subversion debootstrap rsync \
    build-essential

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

First, it is recommended that you create a separate database user for IVLE.
You may use any name for the user. ::

   sudo -u postgres createuser ivleuser     # Answer 'n' to all questions
   sudo -u postgres psql -c "ALTER USER ivleuser WITH ENCRYPTED PASSWORD 'ivle-password';"

Now, you must create a PostgreSQL database, and populate it with the
IVLE schema. You may use any name for the database (here we use ``ivle``). ::

   sudo -u postgres createdb -O ivleuser ivle
   sudo -u postgres createlang plpgsql ivle
   psql -h localhost -W ivle ivleuser < userdb/users.sql

The configuration wizard - ``ivle-config`` - will ask you a series of
questions. You should give the database username and password as configured
above. Apart from database settings, the defaults should be correct
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


Configuring the jail environment
--------------------------------

You will require a self-contained jail environment in which to safely
execute student code. 
Before you can actually build the jail, a few configuration options are
needed. Open up ``/etc/ivle/ivle.conf``, and find the ``[jail]`` section
(**not** the ``[[jails]]`` section).
Add to it: ::

   devmode = True
   suite = jaunty # Replace this with the codename of your Ubuntu release.
   mirror = http://url.to.archive/mirror # Replace with a fast Ubuntu mirror.
   extra_packages = python-configobj, python-svn, python-cjson

.. TODO: Move this around a bit, as the config options required differ for
   the packaged version.

Now we can actually build the jail. The creation process basically downloads
a minimal Ubuntu system and installs it in ``/var/lib/ivle/jails/__base__``.
Note that this could download a couple of hundred megabytes. ::

   sudo ivle-buildjail -r

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


Configuring hostname resolution
--------------------------------

All of IVLE's hostnames need to be resolvable from the local system. For a
production environment, this would be done in DNS. For a development system,
this is usually done in ``/etc/hosts``. Add this line to that file: ::

   127.0.1.1 ivle.localhost public.ivle.localhost svn.ivle.localhost

Code running inside the jail environment also needs to be able to resolve
those names. Add, to ``/var/lib/ivle/jails/__base_build__/etc/hosts``: ::

   127.0.1.1 svn.ivle.localhost

Then refresh the active copy of the jail: ::

   sudo ivle-buildjail


Configuring the user management server
--------------------------------------

You need to have the IVLE user management server (``usrmgt-server``) running
for many parts of IVLE to operate properly, so it should be configured to
start on boot. There is an example init script in
``examples/config/usrmgt-server.init``. For Debian or Ubuntu, copy it to
``/etc/init.d/ivle-usrmgt-server``. Start it now, and set it to start
automatically: ::

   sudo /etc/init.d/ivle-usrmgt-server start
   sudo update-rc.d ivle-usrmgt-server defaults 99


Creating the initial user
-------------------------

The final step in getting a usable IVLE set up is creating a user. You'll
probably want admin privileges - if not, drop the ``--admin``. ::

   sudo ivle-adduser --admin -p password username 'Full Name'

You should then be able to browse to ``http://ivle.localhost/``, and
log in with that username and password.

.. note::
   For more advanced configuration, see :ref:`Configuring IVLE
   <ref-configuring-ivle>`.
