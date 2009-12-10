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


... ivle-buildjail fail with 'Error: Jail contains world writable path'
-----------------------------------------------------------------------

When running :program:`ivle-buildjail` you may occasionally see an error 
like::

    Error: Jail contains world writable path: 
    '/var/lib/ivle/jails/__base_build__/tmp/.ICE-unix'.
    This is a security vulnerability as jail template contents are shared 
    between users. Please either make this path world unwriteable or remove it 
    from the jail.

This means that writable files exist in the Jail template. If left in the jail 
then users would be able to edit a file that is shared between all jail 
instances. The usual solution is just to remove these file from the jail build 
directory and try again.

At present it is not possible to include world writable files outside a user's 
home directory so if this file is deliberately included you will need to 
ensure that it is not world writeable.


... the console return 'Console Restart' messages
-------------------------------------------------

There are three cases where a console may be restarted:

1. **Console Restart: The IVLE console has timed out due to inactivity**

    The Python console process is no longer running. This is most likey due to 
    the console process being automatically terminated due to no messages 
    being sent or received by the console in the previous 15 minutes.

    This message can also be triggered if the console is terminated for 
    another reason (such as being sent :const:`SIGKILL` from the system 
    command line or any other fatal signal).

2. **Console Restart: CPU Time Limit Exceeded**

   To prevent exhaustion of local system resources, Python console processes 
   are set with an CPU Time Limit of 25 seconds of user time (time executing 
   on the CPU rather than real "clock-on-the-wall" time).

   This setting can be configured by changing the values associated with 
   :const:`RLIMIT_CPU` in :file:`bin/trampoline/trampoline.c`.

3. **Console Restart: Communication to console process lost**

    IVLE was unable to understand a response from the console process. This 
    will only happen if the console sends a malformed response and quite 
    likely a bug.

4. **Console Restart: Communication to console process reset**

    IVLE's TCP connection to the console process was reset. May indicate 
    network issues.

