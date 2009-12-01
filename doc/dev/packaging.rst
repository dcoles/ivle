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

*********
Packaging
*********

Source package
==============

The latest copy of trunk can be fetched by running :command:`bzr export 
ivle-latest.tgz lp:ivle`.

Debian Package
==============

A Debian package is currently under development in the 
``lp:~ivle-dev/ivle/debian-packaging`` branch.

William Grant currently maintains a :abbr:`PPA (Personal Package Archive)` of 
IVLE and its dependencies at https://launchpad.net/~wgrant/+archive/ivle.

.. TODO: Are we using this for releases?

Package split
-------------

IVLE will be split into a few packages:

* ``ivle`` will be the all-in-one package, which users can install to get a 
  working IVLE with all tasks on a single node. It will depend on 
  ``ivle-app-server``, ``ivle-usrmgt-server``, *PostgreSQL*, and perform extra 
  automated configuration for the Subversion service.
* ``ivle-app-server`` will contain the web code, trampoline, timount and co., 
  depend upon the packages necessary for an appserver, and perform just the 
  configuration for an appserver (generating config files, scheduling timount 
  runs, etc.)
* ``ivle-usrmgt-server`` will contain and configure the usrmgt-server.
* ``ivle-server-common`` will contain those bits common to the server tasks, 
  but not in the ivle Python package, and not needed in the jail.
* ``ivle-jail`` might not be in the archive, instead being built by 
  ivle-create-jail - it will contain the extra jail scripts.
* ``python-ivle`` will contain the ivle Python package.
