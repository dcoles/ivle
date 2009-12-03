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

.. _ref-faq:

**************************
Frequently Asked Questions
**************************

This is a list of Frequently Asked Questions for IVLE. It answers questions 
about common issues encountered when configuring or running the system.

.. _ref-faq-how:
How can I...
============

... change the Terms of Service notice?
---------------------------------------

You should customize the ToS notice at :file:`/var/lib/ivle/notices/tos.html`.


.. _ref-faq-why:
Why does...
===========

... Apache not restart?
-----------------------

Make sure no console processes are lying around (e.g. sudo killall
python), then restart with ``sudo /etc/init.d/apache2 restart``.  If the issue
persists, try stopping the server and starting it in two separate
steps, so you see the errors reported by the start script.

... IVLE dump me back to the login screen with no error when I try to login?
----------------------------------------------------------------------------

This is usually because IVLE can't save your session information. IVLE saves
sessions to a sessions directory on disk. Unfortunately, this is not currently
configurable in :file:`./setup.py` config. You need to edit the Apache config 
file.

Look for ``PythonOption mod_python.file_session.database_directory``. Make
sure it is set to the place you want. Then, you need to manually make sure
that directory exists.

The default is :file:`/var/lib/ivle/sessions`.

