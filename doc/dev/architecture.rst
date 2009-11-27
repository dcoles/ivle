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

*******************
System Architecture
*******************

IVLE is a complex piece of software that integrates closely with the 
underlying system. It can be considered part web service and part local system 
daemon. Due to the implementation of these parts it is tied to Apache Web 
Server (mainly  due to the use of mod_python) and Linux. 


Jail System
===========

One of the main features of IVLE is it's ability to execute user's code in a 
customised environment that prevents access to other users files or underlying 
file system as well as placing basic resource limits to prevent users from 
accidentally exhausting shared resources such as CPU time and memory.


Trampoline
----------

To each user, it appears that they have their own private Unix filesystem 
containing software, libraries and a home directory to do with what they 
please. This is mainly done by the setuid root program ``trampoline`` (See 
:file:`bin/trampoline/trampoline.c`) which mounts the users home directory, 
sets up the users environment, jumps into the user's jail using the 
:manpage:`chroot(2)` system call and finally drops privileges to the desired 
user and group.

To prevent abuse, ``trampoline`` can only be used by root or one of the uids 
specified when trampoline is built by ``setup.py build`` (defaults to UID 33, 
www-data on Debian systems). Since it's one of two C programs involved in IVLE 
and runs setuid root it is rather secuity sensative.

Base Image Generation
---------------------

All user jails share a common base image that contains the files required for 
both IVLE's operation and for executing user code. This base image is 
generated automatically by the ``ivle-buildjail`` script. This then calls the 
distribution dependant details in :mod:`ivle.jailbuilder` module. At present 
we only support building jails for Debian derived systems using 
:program:`debootstrap`.

The contents of the base image contains a few core packages required for the 
operation of IVLE - Python and the Python CJSON and SVN libraries. Other 
options that can be configured in :file:`/etc/ivle/ivle.conf` are the file 
mirror that debootstrap should use, the suite to build (such as hardy or 
jaunty), extra apt-sources, extra apt keys and any additional packages to 
install.

To prevent users from altering files in the base image we change the 
permissions of :file:`/tmp`, :file:`/var/tmp` and :file:`/var/lock` to not be 
world writeable and check that no other files are world writeable.

Finally we make the user dependent :file:`/etc/passwd` and 
:file:`/etc/ivle/ivle.conf` symlinks to files in the :file:`/home` directory 
so that they will be used when we mount a user's home directory.

Mounting Home Directories
-------------------------

To give the appearance of a private file system we need to merge together a 
user's local home directory with the base image. In the first release of IVLE 
this was done off-line by hardlinking all the files into the target directory, 
but for more than a handful of users this process could take several hours and 
also ran the risk of exhausting inodes on the underlying file system.

The first solution was to use  `AUFS <http://aufs.sourceforge.net/>`_ to mount 
the user's home directory over a read-only version of the base on demand. This 
was implemented as part of ``trampoline`` and used a secondary program 
``timount`` (see :file:`bin/timount/timount.c`) run at regular intervals to 
unmount unused jails. This uses the :const:`MNT_EXPIRE` flag for 
:manpage:`umount(2)` (available since Linux 2.6.8) that only unmounts a 
directory if it hasn't been accessed since the previous call with 
:const:`MNT_EXPIRE`.

While quite effective, AUFS appears to cause NFS caching issues when IVLE is 
run as a cluster as well as questionable inclusion status in newer 
distributions. The current system used in IVLE the much older *bind mount* 
feature which allows directories to be accessible from another location in the 
file system. By carefully read-only bind mounting the jail image and then bind 
mounting the user's :file:`/home` and :file:`/tmp` directory data over the top 
we can create a jail with only three bind mounts and at virtually no 
filesystem overhead.

Entering the Jail
-----------------

Before running the specified program in the users jail we need to 
:manpage:`chroot(2)` into the users jail and update the processes environment 
so that we have the correct environment variables and user/group ids.

At this stage we also may apply a number of resource limits (see 
:manpage:`setrlimit`) to prevent run away processes (such as those containing 
infinite loops or "fork bombs") from exhausting all system resources. The 
default limits are on maximum address space (:const:`RLIMIT_AS`), process data 
space (:const:`RLIMIT_DATA`), core dump size (:const:`RLIMIT_CORE`), CPU time 
(:const:`RLIMIT_CPU`), file size (:const:`RLIMIT_FSIZE`) and number of 
processes that may be spawned (:const:`RLIMIT_NPROC`).

Unfortunately due to glibc's :manpage:`malloc(2)` implementation being able to 
allocate memory using :manpage:`mmap(2)`, :const:`RLIMIT_DATA` does not 
provide an effective limit on the amount of memory that a process can allocate 
(short of applying a kernel patch). Thus the only way to limit memory 
allocations is by placing limits on the address space, but this can cause 
problems with certain applications that allocate far larger address spaces 
than the real memory used. For this reason :const:`RLIMIT_AS` is currently set 
very large.

Console
=======

Version Control
===============

Worksheets
==========

Database
========

Template
========

..  TODO: Not yet merged
    Object Publishing
    =================
