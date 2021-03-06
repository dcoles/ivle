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

... delete a user from IVLE?
----------------------------

This is usually a bad idea since it requires all the references to that user 
to be removed from IVLE. This may have unintended consequences particularly 
with groups or projects but might be required in installations where an 
existing login conflict with a new login (typically encountered when usernames 
are recycled).

The steps to completely remove a user would be:

1. Disable the users account
2. Unmount the users jailmount directory (typically 
   :file:`/var/lib/ivle/jailmounts/LOGIN`)
3. Backup the user's files (typically :file:`/var/lib/ivle/jails/LOGIN`) and 
   remove this directory.
4. Backup the user's repository (typically 
   :file:`/var/lib/ivle/svn/repositories/users/LOGIN` on the subversion 
   server) and remove this directory.
5. Make a backup of the IVLE database (``sudo -u postgres pg_dump ivle > 
   backup.sql``)
6. Either change the users login (``UPDATE login SET login='NEWLOGIN' WHERE 
   login='LOGIN'``) or remove all references to this login in the database

The following lines of SQL should remove all traces of a user ``LOGIN`` from 
the database::

    BEGIN TRANSACTION;
    DELETE FROM exercise_save USING login WHERE
        exercise_save.loginid = login.loginid AND login.login = 'LOGIN';
    DELETE FROM exercise_attempt USING login WHERE
        exercise_attempt.loginid = login.loginid AND login.login = 'LOGIN';
    DELETE FROM project_mark USING login WHERE marker = login.loginid AND
        login.login = 'LOGIN';
    DELETE FROM project_submission USING login WHERE
        submitter = login.loginid AND login.login = 'LOGIN';
    DELETE FROM project_extension USING login WHERE
        approver = login.loginid AND login.login = 'LOGIN';
    DELETE FROM assessed USING login WHERE
        assessed.loginid = login.loginid AND login.login = 'LOGIN';
    DELETE FROM enrolment USING login WHERE
        enrolment.loginid = login.loginid AND login.login = 'LOGIN';
    DELETE FROM group_member USING login WHERE
        group_member.loginid = login.loginid AND login.login = 'LOGIN';
    DELETE FROM group_invitation USING login WHERE
        (group_invitation.loginid = login.loginid OR
        inviter = login.loginid) AND login.login = 'LOGIN';
    DELETE FROM project_group USING login WHERE createdby = login.loginid AND
        login.login = 'LOGIN';
    DELETE FROM login WHERE login='LOGIN';
    COMMIT;

If you do not want to lose group data, a better option may be to reassign the 
user ``LOGIN``'s groups to ``NEWLOGIN`` (one possible option would be to 
create and use a 'nobody' account)::

    BEGIN TRANSACTION;
    DELETE FROM exercise_save USING login WHERE
        exercise_save.loginid = login.loginid AND login.login = 'LOGIN';
    DELETE FROM exercise_attempt USING login WHERE
        exercise_attempt.loginid = login.loginid AND login.login = 'LOGIN';
    UPDATE project_mark SET marker = l2.loginid FROM login AS l1, login AS l2
        WHERE marker = l1.loginid AND l1.login = 'LOGIN' AND l2.login = 
        'NEWLOGIN'
    DELETE FROM project_submission USING login WHERE
        submitter = login.loginid AND login.login = 'LOGIN';
    UPDATE project_extension SET approver = l2.loginid FROM
        login AS l1, login AS l2 WHERE approver = l1.loginid AND
        l1.login = 'LOGIN' AND l2.login='NEWLOGIN';
    DELETE FROM assessed USING login WHERE
        assessed.loginid = login.loginid AND login.login = 'LOGIN';
    DELETE FROM enrolment USING login WHERE
        enrolment.loginid = login.loginid AND login.login = 'LOGIN';
    DELETE FROM group_member USING login WHERE
        group_member.loginid = login.loginid AND login.login = 'LOGIN';
    DELETE FROM group_invitation USING login WHERE
        group_invitation.loginid = login.loginid AND login.login = 'LOGIN';
    UPDATE group_invitation SET inviter = l2.loginid FROM
        login AS l1, login AS l2 WHERE inviter = l1.loginid AND
        l1.login = 'LOGIN' AND l2.login='NEWLOGIN';
    UPDATE project_group SET createdby = l2.loginid FROM
        login AS l1, login AS l2 WHERE createdby = l1.loginid AND
        l1.login = 'LOGIN' AND l2.login = 'NEWLOGIN';
    DELETE FROM login WHERE login='LOGIN';
    COMMIT;


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
that directory exists. If you have multiple slaves, this directory will
need to be shared between them all.

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

