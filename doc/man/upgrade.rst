.. IVLE - Informatics Virtual Learning Environment
   Copyright (C) 2007-2010 The University of Melbourne

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

********
Upgrades
********

Follow these instructions to upgrade your IVLE installation. In the case of a
multi-node installation, follow each instruction on every node unless
otherwise specified.


Shutting down
=============

Before commencing the main upgrade process, ensure that the slave web servers
are inaccessible -- stopping Apache is a good way to be sure. ::

   sudo /etc/init.d/apache2 stop

You should then check for and kill any ``python-console`` process on the
slaves. These are the console backend processes, and may hold resources open
across the upgrade -- that could end badly.


Unmounting user jails
=====================

An upgrade is a good opportunity to purge obsolete jail mounts on each slave.
Unmounting the jails will also reduce the likelihood of problems during the
later jail rebuilds. Take heed of any ``Device busy`` errors -- that normally
indicates that a ``python-console`` process is still running. ::

   sudo ivle-mountallusers -u


Upgrading the code
==================

The next stage of the IVLE upgrade process depends on the installation mode.


Upgrading a source installation
-------------------------------

To upgrade a source installation, update your checkout or extract a new
release tarball.

Then build and install the updated code: ::

   ./setup.py build
   sudo ./setup.py install


Upgrading a packaged installation
---------------------------------

To upgrade an installation from the Ubuntu package, a normal apt upgrade
is sufficient. ::

   sudo apt-get update
   sudo apt-get upgrade


Patching the database
=====================

If the new version has additional database patches, apply each in order on
the master with something like this: ::

   sudo -u postgres psql -d ivle -f userdb/migrations/YYYYMMDD-XX.sql


Upgrading the jail
==================

The code inside the jail will normally need to be kept in sync with that
on the master and slaves. On the upgraded master: ::

   sudo ivle-buildjail -u


Rebuilding user jails
=====================

To ensure that any configuration or structural updates are pushed into the
jails, rebuild them all on the master. ::

   sudo ivle-remakeuser -a

This will preserve the user files (in ``/home/USERNAME``), but rebuild the
external configuration files and filesystem structure.


Changing the media version
==========================

If you've set a media version (in ``ivle.conf``, the ``media`` section's
``version`` value), you'll need to update it on each slave. Set it to a value
that hasn't been used before -- the IVLE version number, for example. Ensure
that it is the same on all slaves.


Restarting the user management server
=====================================

The master's user management server should be restarted after each upgrade. ::

   sudo /etc/init.d/ivle-usrmgt-server restart


Starting everything back up
===========================

Now that the upgrade is done, Apache can be restarted on the slaves. This
should bring IVLE back into service. ::

   sudo /etc/init.d/apache2 start
