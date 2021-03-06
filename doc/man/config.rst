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

This page describes the configuration of IVLE. This consists of populating the 
:file:`ivle.conf` file and configuring Apache to serve the IVLE webapp and 
Subversion repositories.

.. _ref-configuration-options:

Configuration options
=====================

Most of the configuration of IVLE is done by editing the file 
:file:`ivle.conf`, located by default in :file:`/etc/ivle/ivle.conf`. These 
settings are required as part of the :ref:`install process <ref-install>`, 
though the :ref:`admin script <ref-admin-scripts>` :program:`ivle-config` can 
be used to propagate most of these settings.

It uses the `ConfigObj`_ text format which is heavily based on the 'INI' text 
format. Of particular note, lists with single items need to be terminated 
with a ',' otherwise it will be treated as a list of characters (usually not 
what is desired).

.. _ConfigObj: http://www.voidspace.org.uk/python/configobj.html

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
Configuration paths for user :ref:`Jails <ref-jail>`.

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

.. _ref-configuration-policy:

[policy]
--------
Site-specific policy decisions on permissions, etc. These modify the user
roles, as described in :ref:`ref-user-roles`.

.. describe:: tutors_can_enrol_students

    :type: boolean(default=False)

    If True, tutors can enrol any IVLE user as a student in a subject they are
    tutoring. This is disabled by default, as it is generally considered
    unnecessary for tutors to have such power.

.. describe:: tutors_can_edit_worksheets

    :type: boolean(default=True)

    If True, tutors can create and edit worksheets in a subject they are
    tutoring, and can create and edit *any exercise in the system*. This is
    turned on by default, but should be used carefully. Untrusted tutors could
    create site-wide problems.

    (The reason tutors can edit any exercise is because exercises are not
    stored per-subject, so it isn't possible to limit them just to exercises
    for a particular subject.)

[media]
-------
Configuration of media serving.

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

.. describe:: codemirror

    :type: string(default="/usr/share/javascript/codemirror")

    Directory where CodeMirror library is installed.

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
Settings for configuring external user authentication with
:ref:`authentication modules <ref-auth-modules>` and automatic subject
enrollment with :ref:`subject pulldown modules
<ref-subject-pulldown-modules>`.

.. describe:: modules

    :type: string_list(default=list())

    List of :ref:`authentication modules <ref-auth-modules>` to attempt to 
    authenticate with if a user does not have a password set in the local 
    database.

.. describe:: ldap_url

    :type: string(default=None)

    URL of the LDAP server to be used by authentication modules.

.. describe:: ldap_format_string

    :type: string(default=None)


.. describe:: subject_pulldown_modules

    :type: string_list(default=list())

    List of :ref:`subject pulldown modules <ref-subject-pulldown-modules>` to
    be checked when a user signs into IVLE to see what subjects a student is
    enrolled in.

[usrmgt]
--------
Settings for the :ref:`User Management Server <ref-usrmgt-server>`.

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
Options that control how the :ref:`Jail <ref-jail>` is built.

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
    for site specific packages). For example, 'deb 
    http://ppa.launchpad.net/wgrant/ivle/ubuntu/ hardy main,'.

.. describe:: extra_packages

    :type: string_list(default=list())

    A list of extra packages to be installed in addition to the core packages 
    required for IVLE. For example, 'python-scipy, python-networkx,'

.. describe:: extra_keys

    :type: string(default=None)

    Any extra package signing keys to accept as correctly validate installed 
    packages.  Typically used for validating ``extra_sources`` packages.

    Keys can be provided in tripple quoted blocks. For multiple keys, simply 
    concatinate the key blocks. For example::

        extra_keys = '''-----BEGIN PGP PUBLIC KEY BLOCK-----
        Version: SKS 1.0.10

        mI0ESXMxaQEEAMdundmJeTMUcB6fRXGQ3WJH+5hlfj3ehurF3u0ubr4sQpxfJvl6/KV4UcOC
        RvK4aufNInJxKrT6xvzdMNE9z5NO/ZVZdkr2NfcRO/0Yxgmaft9qjxfV+3NEBrvJkqm8ApVO
        hsxFW6VWyeHBELSiNxNGToPp+2g3i5VAlWbtzaapABEBAAG0H0xhdW5jaHBhZCBQUEEgZm9y
        IFdpbGxpYW0gR3JhbnSIRgQQEQIABgUCSXOMJAAKCRABz5LwpyR9xeXXAJ97VdeI3lLDvyM9
        TLeb48Ylj8dWdQCfcOJDRGfjRu9PI2+ekIoV8TqaC0GItgQTAQIAIAUCSXMxaQIbAwYLCQgH
        AwIEFQIIAwQWAgMBAh4BAheAAAoJECp86x2KYmtCEBED/0aRhr7wKmA/nyX2rUN/1dpyYT2T
        khxJT0F7l91/PGRkLUdvcX81ceRcYeiiR1x8N1tL7pwrTWZwaQ/HTHF19ZAXjptnn8zaLKUc
        VwhOrUdFE2FzNo42BWpXQAuJuBCG3DeIXDDuPRvtL+sx7h8PD/DlE5RsTaztkkbWdpkMtJp9
        =5ocD
        -----END PGP PUBLIC KEY BLOCK-----
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        Version: GnuPG v1.4.9 (GNU/Linux)

        mQGiBEFEnz8RBAC7LstGsKD7McXZgd58oN68KquARLBl6rjA2vdhwl77KkPPOr3O
        YeSBH/voUsqausJfDNuTNivOfwceDe50lbhq52ODj4Mx9Jg+4aHn9fmRkIk41i2J
        3hZiIGPACY/FsSlRq1AhBH2wZG1lQ45W/p77AeARRehYKJP9HY+1h/uihwCgrVE2
        VzACJLuZWHbDsPoJaNQjiFcEAKbUF1rMyjd1xJM7bZeXbs8c+ohUo/ywSI/OIr8n
        <SNIP>
        RwIbDAAKCRBAl26vQ30FtdxYAJsFjU+xbex7gevyGQ2/mhqidES4MwCggqQyo+w1
        Twx6DKLF+3rF5nf1F3Q=
        =PBAe
        -----END PGP PUBLIC KEY BLOCK-----
        '''


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
Apache is used in IVLE for hosting of the IVLE web application and hosting 
Subversion repositories over WebDAV. Typically the Subversion repository will 
run on the Master server and the Web Application will be run on a collection 
of slaves.  It is also possible to combine the two function together to run as 
a standalone server.


Web Application
---------------
The IVLE web application runs on Apache using ``mod_python``. An example 
configuration for normal HTTP is provided in the file 
:file:`examples/config/apache.conf` and an example configuration for using 
Secure HTTP using SSL certificates is provided in the file 
:file:`examples/config/apache-ssl.conf`.

At minimum the following settings must be specified:

.. describe:: ServerName

    Should be the formal hostname of the server, typically one that users will 
    use to access IVLE. For example, 'ivle.org'.

.. describe:: ServerAlias

    Should be set to the value of ``[urls] public_host`` that is specified in 
    :file:`ivle.conf`. This is to ensure that Apache will correctly handle 
    requests for the public content.

.. describe:: SetHandler

    Must be ``mod_python``

.. describe:: PythonHandler

    Must be ``ivle.dispatch``

.. describe:: PythonOption mod_python.file_session.database_directory

    Session directory for mod_python. This must be a shared directory between 
    all Slave servers, in particular when operating through a load balancer.  
    If not provided then users will encounter inconsistent behavior such as 
    being thrown back to the login screen after logging in.

Optional settings are:

.. describe:: PythonOption mod_python.session.cookie_name

    The name to be set for cookies rather than the one automatically generated 
    by mod_python. For example, 'ivle'.

.. describe:: PythonDebug

    If this option is set, any uncaught errors from mod_python will be sent to 
    the browser rather than being sent to the error log. It is recommended 
    that this setting is only used for development or debugging.

Subversion Repository
---------------------
IVLE also uses Apache to provide HTTP access to user's Subversion repositories 
using ``mod_dav_svn``. Typically this is run on a single, stand alone server; 
though it may be run in conjunction with the Web Application.  An example 
configuration is provided in the file :file:`examples/config/apache-svn.conf`.  
IVLE will automatically generate password hash and repository permission files 
that are used to control access to the repositories.

IVLE expects to find the paths ``users/`` and ``groups/`` at the URL provided 
by the value of ``[urls] svn_addr`` set in :file:`ivle.conf`. Thus there 
should be two ``Location`` clauses configured, one for users and one for 
groups.

User Repositories
~~~~~~~~~~~~~~~~~

.. describe:: DAV

    Must be ``svn``

.. describe:: SVNParentPath

    Directory where user repositories are stored. Should be the value of 
    ``[path] [[svn]] repo_path`` in :file:`ivle.conf` with 'users' appended.  
    For example, '/var/lib/ivle/svn/repositories/users'.

.. describe:: AuthzSVNAccessFile

    Location of the configuration file used to assign permissions to user 
    repositories. Should be the same value as ``[path] [[svn]] conf`` in 
    :file:`ivle.conf`.

.. describe:: Require

    Must be ``valid-user``

.. describe:: AuthType

    Must be ``Basic``

.. describe:: AuthName

    The name that should appear on authentication requests. For example, 'IVLE 
    Subversion repository'.

.. describe:: AuthUserFile

    Location of the password hash file for Subversion users. Should be the 
    same as the value of ``[path] [[svn]] auth_ivle``. For example, 
    '/var/lib/ivle/svn/ivle.auth'.

Group Repositories
~~~~~~~~~~~~~~~~~~

.. describe:: DAV

    Must be ``svn``

.. describe:: SVNParentPath

    Directory where user repositories are stored. Should be the value of 
    ``[path] [[svn]] repo_path`` in :file:`ivle.conf` with 'groups' appended.  
    For example, '/var/lib/ivle/svn/repositories/groups'.

.. describe:: AuthzSVNAccessFile

    Location of the configuration file used to assign permissions to group 
    repositories. Should be the same value as ``[path] [[svn]] group_conf`` in 
    :file:`ivle.conf`.

.. describe:: Require

    Must be ``valid-user``

.. describe:: AuthType

    Must be ``Basic``

.. describe:: AuthName

    The name that should appear on authentication requests. For example, 'IVLE 
    Subversion repository'.

.. describe:: AuthUserFile

    Location of the password hash file for Subversion users. Should be the 
    same as the value of ``[path] [[svn]] auth_ivle``. For example, 
    '/var/lib/ivle/svn/ivle.auth'.
