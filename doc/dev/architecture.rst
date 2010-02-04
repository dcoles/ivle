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
Server (mainly due to the use of mod_python) and Linux.


Dispatch
========

IVLE uses mod_python_ to allow Python scripts to be called from Apache. We 
register the :mod:`ivle.dispatch` module as the ``PythonHandler`` in the 
associated VirtualHost, allowing us to intercept all HTTP requests to the web 
server.

The :mod:`ivle.dispatch` module is responsible for mapping requests from the 
client to the correct application plugin. Plugins can be specified by placing  
a :file:`*.conf` file into the :file:`/etc/ivle/plugins.d/` directory 
containing lines of the form :samp:`[{plugin_module}#{classname}]`.

.. TODO: Document Plugin Format and Routing Strings

In future, this may be ported to a WSGI (:pep:`333`) based dispatch to allow 
IVLE to be run on web servers other than Apache.

.. _mod_python: http://www.modpython.org/


Templating
----------
IVLE uses the Genshi_ XHTML template system to generate all HTML pages. We
have an inheritance-based "views" system. :class:`BaseView` is a class from
which all views derive.

There are 3 sub-types of :class:`BaseView` (more can be implemented if 
necessary):

* XHTML-Templated
    * browser, console, debuginfo, diff, forum, groups, help, home, logout, 
      settings, subjects, svnlog, tos, tutorial
* Raw byte streaming
    * download, server
* JSON service
    * consoleservice, fileservice, tutorialservice, userservice 

The apps each derive from one of the above.

.. note::
   IVLE used to write its HTML output as a raw stream to an output file, until
   it was refactored to use Genshi. All apps which haven't yet been refactored
   properly were ported to use the "raw byte streaming" view.

.. _Genshi: http://genshi.edgewall.org/


.. _ref-jail:

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
please. This is mainly done by the setuid root program ``trampoline`` which 
mounts the users home directory, sets up the users environment, jumps into the 
user's jail using the :manpage:`chroot(2)` system call and finally drops 
privileges to the desired user and group.

To prevent abuse, ``trampoline`` can only be used by root or one of the uids 
specified when trampoline is built by ``setup.py build`` (defaults to UID 33, 
www-data on Debian systems). Since it's one of two C programs involved in IVLE 
and runs setuid root it is rather security sensitive.

.. seealso:: Source code :file:`bin/trampoline/trampoline.c`


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
user's local home directory with the base image.
To achieve this, IVLE uses the *bind mount* feature of Linux, which allows
directories to be accessible from another location in the file system. By
carefully bind-mounting the jail image as read-only and then bind-mounting the
user's :file:`/home` and :file:`/tmp` directory data over the top, we create a
jail with only three bind mounts and at virtually no file system overhead.

.. note::
   IVLE has historically used numerous solutions to this problem, which are
   chronicled here to avoid the same mistakes being made again.

   In the first release of IVLE this was done offline by hard-linking all the
   files into the target directory, but for a large number of users, this
   process can take several hours, and also runs the risk of exhausting
   the number of inodes on the underlying file system.

   The second solution was to use `AUFS <http://aufs.sourceforge.net/>`_ to
   mount the user's home directory over a read-only version of the base on
   demand. This was implemented as part of ``trampoline`` and used a secondary
   program ``timount`` (see :file:`bin/timount/timount.c`), run at regular
   intervals, to unmount unused jails. This used the :const:`MNT_EXPIRE` flag
   for :manpage:`umount(2)` (available since Linux 2.6.8) that only unmounts a
   directory if it hasn't been accessed since the previous call with
   :const:`MNT_EXPIRE`.

   While quite effective, AUFS appeared to cause NFS caching issues when IVLE
   was run as a cluster, and as its inclusion status in future Linux
   distributions is questionable, the developers elected to use the much older
   bind mount feature instead.

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


.. _ref-python-console:

Python Console
==============

IVLE provides a web based programming console, exposing similar features to 
Python's command line console. It is built around the
:file:`services/python-console` script, which opens up a socket on a random
port to which `JSON`_ encoded chat requests can be made.

A new console is typically launched on demand by the web client to the HTTP
API, which in turn calls the wrapper class :class:`ivle.console.Console` to
start a new console in the user's jail.

Subsequent requests from the same in-browser console connect to the existing
console process. This is achieved by storing a string on the client which
identifies the server address and port. The client then makes requests
through the load balancer, sending this string through to an arbitrary slave
which forwards the request to the identified console.

This means that all slaves need access to all ports on every other slave.

.. _JSON: http://json.org


.. _ref-usrmgt-server:

User Management Server
======================

The **User Management Server** is a daemon responsible for handling privileged 
actions on IVLE and should be launched along with IVLE. It is primarily 
responsible for:

* Creating user jails, Subversion repositories, and Subversion authentication 
  credentials.
* Creating group Subversion repositories.
* Rebuilding Subversion authorization files. 

Communication with the Server is done using the :ref:`Chat Protocol
<ref-chat>`.  To prevent unauthorized use, communication with the User
Management Server requires that a *shared secret* be used to communicate with
the server.  This secret is stored in the `magic` variable in the `[usrmgt]`
section of :file:`/etc/ivle/ivle.conf`.

The User Management Server is called almost exclusively from the 
:mod:`ivle.webapp.userservice` module.

.. seealso:: Source code :file:`services/usrmgt-server`

.. _ref-chat:

Chat Protocol
=============

**Chat** is our JSON_-based client/server communication protocol used in
communicating to :ref:`Python Console <ref-python-console>` processes and
:ref:`User Management Server <ref-usrmgt-server>`.  Since it is JSON-based it
can be called from either Python or JavaScript.

Protocol
--------
The protocol is a fairly simple client/server based one consisting of a single 
JSON object. Before communication starts a shared secret :const:`MAGIC` must 
be  known by both parties. The shared secret is then used to form a 
'keyed-Hash Message Authentication Code' to ensure that the content is valid 
and not been modified in transit.

The client request takes the following form::

    {
        "content": DATA,
        "digest": HASH
    }

where :const:`DATA` is any valid JSON value and :const:`HASH` is an string 
containing the MD5 hash of the :const:`DATA` appended to :const:`MAGIC` and 
then hex encoded.

The server will respond with a JSON value corresponding to the request.
If an error occurs then a special JSON object will be returned of the 
following form::

    {
        "type": NAME,
        "value": VALUE,
        "traceback": TRACEBACK
    }

where :const:`NAME` is a JSON string of the exception type (such as 
'AttributeError'), :const:`VALUE` is the string value associated with the 
exception and :const:`TRACEBACK` is a string of the traceback generated by the 
server's exception handler.

.. seealso:: Source code :file:`ivle/chat.py`


Version Control
===============

Along with traditional file system access, IVLE allows users to version their 
files using Subversion_. Much like how Subversion workspaces are used on a 
standard desktop, workspaces are checked out into users home directories where 
they can be manipulated through a series of AJAX requests to the 
``fileservice`` app.

Like all other user file system actions, version control actions need to be 
executed inside the user's :ref:`jail <ref-jail>`. Requests are made to the 
``fileservice`` app in :mod:`ivle.webapp.fileservice` which then calls the 
``fileservice`` CGI script using ``trampoline``. This script is simply a 
wrapper around :mod:`ivle.fileservice_lib` which actually contains the code to 
handle each of the actions.

Manipulation of the Subversion workspaces is done using the pysvn_ library. 

.. _Subversion: http://subversion.tigris.org/
.. _pysvn: http://pysvn.tigris.org/


Repositories
------------

Each user is allocated a Subversion repository when their :ref:`Jail 
<ref-jail>` is created by the :ref:`User Management Server 
<ref-usrmgt-server>`. Repository are stored in the location specified by 
``[paths] [[svn]] repo_path`` in :file:`/etc/ivle/ivle.conf` (by default 
:file:`/var/lib/ivle/svn/repositories/`). User repositories are stored in the 
:samp:`users/{USERNAME}/` subdirectory and group repositories in 
:samp:`groups/{SUBJECT}_{YEAR}_{SEMESTER}_{GROUP}`.

.. warning::

    While it would be possible to give users direct access to their repository 
    using Subversion's file backend, this would allow users to potentially 
    modify the history of any repository that they had access to. To ensure 
    repository integrity, all Subversion interaction must be done remotely.


Subversion WebDAV
-----------------

These repositories are served by Apache using ``mod_dav_svn`` allowing access 
over Subversion's WebDAV HTTP or HTTPS backends. Users are authenticated using 
a randomly generated key which is stored in the database and is made available 
to each user inside their Jail (``svn_pass`` property inside 
:file:`/home/.ivle.conf`). This key is automatically provided when doing 
Subversion actions, but can be manually entered when accessing a users 
repository from an external Subversion client such as with :samp:`svn checkout 
{svn_addr}/users/{USERNAME}/ workspace`.

Repository permissions for ``AuthzSVNAccessFILE`` are automatically generated 
and placed in the file located at ``[paths] [[svn]] conf`` for user 
repositories and ``[paths] [[svn]] group_conf`` for group repositories. User 
authentication keys for ``AuthUserFile`` are stored in the file located at 
``[path] [[svn]] auth_ivle``. These will be regenerated each time user or 
group repository settings change.


Worksheets
==========

Database
========

..  TODO: Not yet merged
    Object Publishing
    =================
