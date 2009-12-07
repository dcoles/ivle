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

.. _ref-configuring-ivle:

****************
Configuring IVLE
****************

This page describes the configuration of IVLE, which is done by editing the
file :file:`ivle.conf`, located by default in :file:`/etc/ivle/ivle.conf`.

Configuration options
=====================

[urls]
------
Configuration of URLs used by the IVLE webapp.

.. describe:: root

    :type: string(default="/")

    Path on HTTP server that IVLE is served from.

.. describe:: public_host

    :type: string

    The server goes into "public mode" if the browser sends a request with 
    this host. This is for security reasons - we only serve public student 
    files on a separate domain to the main IVLE site.
    Public mode does not use cookies, and serves only public content.
    Private mode (normal mode) requires login, and only serves files relevant 
    to the logged-in user. e.g. 'public.ivle.org'

.. describe:: svn_addr

    :type: string

    The base url for accessing subversion repositories. e.g.  
    'http://svn.ivle.org'

[paths]
-------
Configuration for IVLE installation and data paths.

.. describe:: prefix

    :type: string(default="/usr/local")

    The prefix that is prepended to installation paths.

.. describe:: data

    :type: string(default="/var/lib/ivle")

    Directory where IVLE data such as user jails will be stored.

.. describe:: logs

    :type: string(default="/var/log/ivle")

    Directory where IVLE log files such as :file:`ivle_error.log` will be 
    saved.
.. describe:: share

    :type: string(default="${prefix}/share/ivle")

    Directory where IVLE shared data such as ``usrmgt-server``, 
    ``python-console`` and services will be installed.

.. describe:: lib

    :type: string(default="${prefix}/lib/ivle")

    Directory where IVLE libraries such as ``trampoline`` and ``timount`` will 
    be installed.

[[jails]]
~~~~~~~~~
Configuration paths for user `Jails <ref-jail>`_.

.. describe:: mounts

    :type: string(default="${data}/jailmounts"))

    Directory where complete jails will be mounted.


.. describe:: src

    :type: string(default="${data}/jails")

    Directory where user specific jail content will be stored.

.. describe:: template

    :type: string(default="${src}/__base__")

    Directory where template file system for each jail will be stored.

.. describe:: template_build

    :type: string(default="${src}/__base_build__")

    Directory where template file system will be built before being moved to 
    the ``template`` directory.

[[svn]]
~~~~~~~
Configuration paths for Subversion repositories.

.. describe:: base

    :type: string(default="${data}/svn")

    Directory where Subversion data will be stored

.. describe:: conf

    :type: string(default="${base}/svn.conf")

    Location of Subversion WebDAV AuthzSVNAccessFile configuration file for 
    user repositories will be stored.

.. describe:: group_conf

    :type: string(default="${base}/svn-group.conf")

    Location of Subversion WebDAV AuthzSVNAccessFile configuration file for 
    group repositories will be stored.

.. describe:: repo_path

    :type: string(default="${base}/repositories")

    Location where user and group repositories will be stored.

.. describe:: auth_ivle

    :type: string(default="${base}/ivle.auth")

    Location where Subversion WebDAV AuthUserFile password hash file will be 
    stored.

[media]
-------
Configuration of `media serving <ref-media-serving>`_.

.. describe:: version

    :type: string(default=None)

    Media files such as images, CSS and JavaScript are aggressively cached in 
    IVLE. If this value is set then IVLE will send media URLs containing this 
    version number and content will be served with an ``Expires`` header set a 
    year in the future. This means that the client should only request a media 
    URL once and use the cached copy from then on.  This version number should 
    be incremented each time any media is changed (typically this should just 
    be set to the IVLE release number) so that updated media will be sent to 
    clients.

    If not provided or set to :const:`None`, IVLE will use standard browser 
    caching.

[[externals]]
~~~~~~~~~~~~~
Configuration details for external media dependencies used by IVLE.

.. describe:: jquery

    :type: string(default="/usr/share/javascript/jquery")

    Directory where jQuery library is installed.


[database]
----------
Configuration for the PostgreSQL database that IVLE uses.

.. describe:: host

    :type: string(default="localhost")

    Hostname of database IVLE server.

.. describe:: port

    :type: integer(default=5432)

    Port the database runs on.

.. describe:: name

    :type: string(default="ivle")

    Name of the IVLE database on the database server.

.. describe:: username

    :type: string

    Username which IVLE uses on the database server.

.. describe:: password

    :type: string

    Password which IVLE uses for authentication with the database server.

[auth]
------
Settings for configuring external user authentication with `authentication 
modules <ref-auth-modules>`_ and automatic subject enrollment with `subject 
pulldown modules <ref-subject-pulldown-modules>`_.

.. describe:: modules

    :type: string_list(default=list())

    List of `authentication modules <ref-auth-modules>`_ to attempt to 
    authenticate with if a user does not have a password set in the local 
    database.

.. describe:: ldap_url

    :type: string(default=None)

    URL of the LDAP server to be used by authentication modules.

.. describe:: ldap_format_string

    :type: string(default=None)


.. describe:: subject_pulldown_modules

    :type: string_list(default=list())

    List of `subject pulldown modules <ref-subject-pulldown-modules>`_ to be 
    checked when a user signs into IVLE to see what subjects a student is 
    enrolled in.

[usrmgt]
--------
Settings for the `User Management Server <ref-usrmgt-server>`_.

.. describe:: host

    :type: string(default="localhost")

    The hostname where the User Management Server is running.

.. describe:: port

    :type: integer(default=2178)

    The port that the User Management Server is running on.

.. describe:: magic

    :type: string

    The shared secret used to secure communication between IVLE Web 
    Application and the User Management Server.

[jail]
------
Options that control how the `Jail <ref-jail>`_ is built.

.. describe:: devmode

    :type: boolean(default=False)

    If set, copies IVLE files from the local machine into the jail rather than  
    installing them from a package.

    .. note::

        If the Python site packages directory differs between the local 
        machine and the jail (such as if different versions of Python are 
        installed) you will need to supply the site packages to be installed 
        with the ``--python-site-packages`` option to ``ivle-buildjail``.

.. describe:: suite

    :type: string(default="hardy")

    Which suite the jail will build with. This need not be the same as what 
    the local machine is running.

.. describe:: mirror

    :type: string(default="http://archive.ubuntu.com/ubuntu")

    The location of a HTTP mirror containing the specified suite.

.. describe:: extra_sources

    :type: string_list(default=list())

    A list of extra source locations to be added to the jail builder (such as 
    for site specific packages).

.. describe:: extra_packages

    :type: string_list(default=list())

    A list of extra packages to be installed in addition to the core packages 
    required for IVLE.

.. FIXME: Is this correct. Is it extra user packages (such as
    python-scipy) or all packages that aren't in a standard debootstrap build 
    (such as python-svn and python-cjson)?.

.. describe:: extra_keys

    :type: string(default=None)

    Any extra package signing keys to accept as correctly validate installed 
    packages.  Typically used for validating ``extra_sources`` packages.
    
    .. note:: Cannot have triple-quoted list members.


[user_info]
-----------
User specific settings that are added to a user's :file:`ivle.conf` file 
inside their jail.

.. warning::

    This should be in a user-specific place but since we're worried a user
    may delete his/her .conf file, we put it here for now). These properties 
    **should not** be set in the server's :file:`/etc/ivle/ivle.conf`.

.. describe:: login

    :type: string(default=None)

    The login name of the user.

.. describe:: svn_pass

    :type: string(default=None)

    The key used to access repositories on the Subversion server.


Apache configuration
====================
