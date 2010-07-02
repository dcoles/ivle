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

.. If this list changes, you also need to change the list below, and
   the list in bin/ivle-dev-setup.

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
   + Storm (``python-storm``)
* jQuery (``libjs-jquery``)
* CodeMirror (``libjs-codemirror``)
* PostgreSQL 8.3 or later (``postgresql``)
* Subversion (``subversion``)
* debootstrap (``debootstrap``)
* rsync (``rsync``)
* GCC and related build machinery (``build-essential``)

Master versus slave servers
===========================

IVLE is normally deployed in a cluster of several machines, split into
two different roles: master and slave.

There must be exactly one master server per cluster. The master normally
runs the PostgreSQL database server, the Subversion server, and the IVLE User
Management Server (``ivle-usrmgt-server``). It might also export shared data
directories to the slaves over NFS.

There may be any number of slaves in a cluster. They run the IVLE web
application, which also starts console host processes. Each slave makes use
of the shared services on the master.

For a small instance a slave may be run on the same machine as the master.
This is the setup described in the source installation section, while the
Ubuntu package installation section describes a multi-node configuration.


Installing from source
======================

When setting up a development IVLE environment on Ubuntu 9.04 or later,
there are scripts to automate most of the process. First get and extract
`a release tarball <https://launchpad.net/ivle/+download>`_, or check out
the latest code from the Bazaar branch: ::

   bzr get lp:ivle

This will create a new directory, ``ivle``, containing a pristine
source tree. The remaining steps assume that you are in this new
directory.


Automated setup
---------------

The ``ivle-dev-setup`` script will configure PostgreSQL, Apache, IVLE
and the filesystem to cooperate, getting you most of the way to a
working system in just one step: ::

   bin/ivle-dev-setup

.. warning::
   This reconfigures parts of your system, and has the potential to
   break other applications using Apache or PostgreSQL. It may also
   fail to execute if you have existing incompatible configurations
   of those services.
   

This may take a few minutes, and will ask you to confirm installation
of the dependency packages.

Upon completion, you must build a self-contained jail in which to run
untrusted user code. ``ivle-dev-setup`` will have configured most of
the necessary settings, but you may wish to use a local Ubuntu mirror
to improve speed or minimise download costs. If you don't wish to use
a special mirror, you may omit the first step. ::

   sudo ivle-config --jail/mirror http://url.to.mirror/ubuntu
   sudo ivle-buildjail -r

.. warning::
   ``ivle-buildjail`` will download a large volume of package data --
   potentially some hundreds of megabytes.

``ivle-buildjail`` will download, unpack and install a minimal Ubuntu
system and configure it for IVLE usage. This could take a while.

Once the jail has been successfully built, IVLE is up and running,
but with no user accounts or other data in place. For development
or demonstration purposes, sample data (including fictitious users,
subjects, and projects) can be loaded.

For other environments, it may be more appropriate to start with an
empty database and just create users as required.

To load the sample data: ::

   sudo ivle-loadsampledata examples/db/sample.sql

.. warning::
   If you answer 'yes' to the ``ivle-loadsampledata`` prompt, any
   existing data in your IVLE database will be **permanently
   destroyed**.

... or to add a new admin user: ::

   sudo ivle-adduser --admin -p password username 'Full Name'

You should then be able to browse to http://ivle.localhost/, and
log in with username ``admin`` and password ``password``, or the
username and password that you gave to ``ivle-adduser``.


Manual steps
------------

If the automatic installation scripts do not work, or if you want more
control over the whole process, these manual steps are probably for
you. But you need not read this section at all if you were able to log
in after following the steps above.

.. If this list changes, you also need to change the list above, and
   the command in bin/ivle-dev-setup.

If you want to grab all of the required packages in one command, use::

    sudo apt-get install apache2 libapache2-mod-python libapache2-svn \
    python2.6 python-cjson python-configobj python-docutils python-epydoc \
    python-formencode python-genshi python-psycopg2 python-svn python-storm \
    libjs-jquery postgresql subversion debootstrap rsync build-essential

As IVLE needs to compile some binaries, you must first build, then
install it. From the source directory created earlier: ::

   ./setup.py build
   sudo ./setup.py install

.. _database-setup:

Setting up the database
~~~~~~~~~~~~~~~~~~~~~~~

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


Creating the data tree
~~~~~~~~~~~~~~~~~~~~~~

IVLE needs a directory hierarchy in which to store filesystem data, which
by default lives in ``/var/lib/ivle``. Create it now. ::

   sudo ivle-createdatadirs


Configuring the jail environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You will require a self-contained jail environment in which to safely
execute student code. 
Before you can actually build the jail, a few configuration options are
needed. Open up ``/etc/ivle/ivle.conf``, and find the ``[jail]`` section
(**not** the ``[[jails]]`` section).
Add to it: ::

   devmode = True
   suite = jaunty # Replace this with the codename of your Ubuntu release.
   mirror = http://url.to.archive/mirror # Replace with a fast Ubuntu mirror.

.. TODO: Move this around a bit, as the config options required differ for
   the packaged version.

Now we can actually build the jail. The creation process basically downloads
a minimal Ubuntu system and installs it in ``/var/lib/ivle/jails/__base__``.
Note that this could download a couple of hundred megabytes. ::

   sudo ivle-buildjail -r


Configuring Apache
~~~~~~~~~~~~~~~~~~

IVLE makes use of two Apache virtual hosts: one for the application itself,
and one for the Subversion services. There are example configuration files
in ``examples/config/apache.conf`` and ``examples/config/apache-svn.conf``,
which will run IVLE at http://ivle.localhost/.

On a Debian or Ubuntu system, just copy those two files into
``/etc/apache2/sites-available`` under appropriate names (eg. ``ivle`` and
``ivle-svn``). Then you need to activate them: ::

   sudo a2ensite ivle
   sudo a2ensite ivle-svn
   sudo /etc/init.d/apache2 reload


Configuring hostname resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You need to have the IVLE user management server (``usrmgt-server``) running
for many parts of IVLE to operate properly, so it should be configured to
start on boot. There is an example init script in
``examples/config/usrmgt-server.init``. For Debian or Ubuntu, copy it to
``/etc/init.d/ivle-usrmgt-server``. Start it now, and set it to start
automatically: ::

   sudo /etc/init.d/ivle-usrmgt-server start
   sudo update-rc.d ivle-usrmgt-server defaults 99


Creating the initial user
~~~~~~~~~~~~~~~~~~~~~~~~~

The final step in getting a usable IVLE set up is creating a user. You'll
probably want admin privileges - if not, drop the ``--admin``. ::

   sudo ivle-adduser --admin -p PASSWORD USERNAME 'FULL NAME'

You should then be able to browse to http://ivle.localhost/, and
log in with that username and password.

*Alternatively*, you may wish to import the IVLE sample data, for a complete
working IVLE environment (not for production use). See :ref:`sample-data`.

.. note::
   For more advanced configuration, see :ref:`Configuring IVLE
   <ref-configuring-ivle>`.



Installing from an Ubuntu package
=================================

IVLE is packaged in `a Launchpad PPA <https://launchpad.net/~unimelb-ivle/+archive/production>`_,
providing a more managed installation and upgrade mechanism than a source
installation.

These instructions document the process to install a production-ready
multi-node IVLE cluster. They expect that you have three domain names:
one for the main IVLE web UI, one for the Subversion service, and one
for serving user files publicly.

.. warning::
   By design the public domain may have arbitrary user-generated content
   served. Because of this, it should not have any domain with sensitive
   cookies as a suffix, including the main IVLE web UI. Be very careful
   with your choice here.


Shared setup
------------

All master and slave nodes need to have access to the IVLE PPA.
`Visit it <https://launchpad.net/~unimelb-ivle/+archive/production>`_ and
follow the installation instructions on all involved systems.


Master setup
------------

Setting up the database server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The master server runs the central IVLE PostgreSQL database. ::

   sudo apt-get install postgresql

Ubuntu's default PostgreSQL configuration doesn't permit remote access,
so we need to tweak it to allow password access from our slave. In
``/etc/postgresql/8.3/main/postgresql.conf``, find the ``listen_addresses``
option, and ensure it is set to ``*``. In
``/etc/postgresql/8.3/main/pg_hba.conf`` add a line like the following to the
end. This example will allow any host in the ``1.2.3.4/24`` subnet to
authenticate with a password as the ``ivle`` user to the ``ivle`` database. ::

   host    ivle        ivle        1.2.3.4/24      md5

Then restart PostgreSQL, and the slaves should be able to see the database. ::

   sudo /etc/init.d/postgresql-8.3 restart


Installing and configuring IVLE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can now install IVLE. The installation process will ask you a few questons.
Answer that this host is a **master**, let it generate a random usrmgt-server
secret, elect to manage the database with ``dbconfig-common``, and use a
random password. ::

   sudo apt-get install ivle

Once that's done, we have a couple of additional configuration items to set:
the URLs discussed earlier. Open up ``/etc/ivle/ivle.conf``, 
and replace ``public.ivle.localhost`` and ``svn.ivle.localhost`` with the
correct domain names.

Make sure you restart the ``usrmgt-server`` afterwards, or newly created users
may inherit the old domain names. ::

   sudo /etc/init.d/usrmgt-server restart


Sharing data between the servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As well as its relational database, IVLE has a data hierarchy on the
fileystem. Two part of this (``/var/lib/ivle/jails`` and
``/var/lib/ivle/sessions``) must be shared between the master and all of the
slaves. It doesn't matter how you achieve this, but a reasonable method is
described here: exporting over NFS from the master.

We'll first create a tree (``/export/ivle`` in this example, but it can be
whatever you want) to be exported to the slaves, move the existing data
directories into it, and symlink them back into place. ::

   sudo mkdir /export/ivle
   sudo mv /var/lib/ivle/{sessions,jails} /export/ivle
   sudo ln -s /export/ivle/{sessions,jails} /var/lib/ivle

Next install an NFS server. ::

   sudo apt-get install nfs-kernel-server

Now we can export the directory we created earlier across the network.
Add something like the following line to ``/etc/exports``. ``someslave``
should be replaced with the hostname, IP address, or subnet of your
slave(s). ::

   /export/ivle		someslave(rw,sync)

Make sure you inform the kernel of the new export. ::

   sudo exportfs -a


Configuring Apache
~~~~~~~~~~~~~~~~~~

The master serves Subversion repositories through Apache on the Subversion
domain name that was discussed above. ::

   sudo cp /usr/share/doc/ivle/apache-svn.conf /etc/apache2/sites-available/ivle-svn
   sudo a2ensite ivle-svn

Edit ``/etc/apache2/sites-available/ivle-svn``, ensuring that the
``ServerName`` matches your chosen domain name. Then reload Apache's
configuration. ::

   sudo /etc/init.d/apache2 reload


Setting up a jail environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IVLE requires that a base jail be provided, on top of which all of the
individual user jails are constructed in order to safely execute user code.

We need to change some configuration options before we can build a working
jail. First set the mirror and Ubuntu release -- make sure you replace the
URL and release code name with an Ubuntu mirror and your Ubuntu release. ::

   sudo ivle-config --jail/mirror http://url.to.mirror/ubuntu --jail/suite hardy

Now comes the ugly bit: we need to tell the jail builder where to get the
IVLE code that must be present in the jail. If you're using the production
PPA, the following ``/etc/ivle/ivle.conf`` snippet will work. If you're not,
you'll have to replace the ``extra_keys`` and ``extra_sources`` values ::

   [jail]
   extra_keys = '''
   -----BEGIN PGP PUBLIC KEY BLOCK-----
   Version: SKS 1.0.10
   
   mI0ES2pQKAEEANiscebT7+SFnvpN8nABcwT5nEV6psUOF8CcIIrz3iv6b6wA3lYd0DzbD7RD
   fs1MNriEHHgqPF6EUhGrkk1165Oqi+lULdjgL0Fzi3GFvLV9F8+BtL3wt3+MM7YC+aTS1nhF
   dQcPpnhNAJagW5gR4dIc4w87sNquxgCdJeJn/N3XABEBAAG0KkxhdW5jaHBhZCBVbml2ZXJz
   aXR5IG9mIE1lbGJvdXJuZSBJVkxFIFBQQYi2BBMBAgAgBQJLalAoAhsDBgsJCAcDAgQVAggD
   BBYCAwECHgECF4AACgkQVwp7ATtnautCMgP8C6PbLNyx9akgbiwhakFfGaEbxGFCo1EAUE7v
   FgdelJSEkeQLAn4WoANpixuojNi++PEDis22S4tz+ZC6G0dRU9Pcc1bb4xUgphR83QTcufH7
   5EagfTf5lLIWaLdg5f/NeuHHrKvwKvPVkNJ3ShQejFB/xWGpqe2Rr7Rscm9lT0Q=
   =TJYw
   -----END PGP PUBLIC KEY BLOCK-----
   '''
   extra_packages = ivle-services,
   extra_sources = deb http://ppa.launchpad.net/unimelb-ivle/production/ubuntu hardy main,

Now we can build the jail. This will download lots of packages, and install
a minimal Ubuntu system in ``/var/lib/ivle/jails/__base__``. ::

   sudo ivle-buildjail -r

You should now have a functional master.


Creating the initial user
~~~~~~~~~~~~~~~~~~~~~~~~~

The last master step for getting a usable IVLE set up is creating a user.
You'll probably want admin privileges - if not, drop the ``--admin``. ::

   sudo ivle-adduser --admin -p PASSWORD USERNAME 'FULL NAME'

You can then visit your IVLE web UI domain and login in with the username
and password.


Slave setup
-----------

Installing and configuring IVLE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We need to tell the database configuration assistant that we want to connect
to a remote database. The second command will also ask you whether you want to
store administrative passwords: say no here. ::

   sudo apt-get install dbconfig-common
   sudo dpkg-reconfigure dbconfig-common

We are going to need some details from the master for authentication purposes.
Grab the ``password`` value from the ``database`` section, and the ``magic``
value from the ``usrmgt`` section of the master's ``/etc/ivle/ivle.conf``.

Now we can install IVLE. Advise the installer that this machine is not a
master, and use the details retrieved from the master to answer the rest of
the questions. ::

   sudo apt-get install ivle

Once the installation has completed, make the same configuration changes as on
the master: set the domain names in ``ivle.conf`` to real values.

For maximum performance, you should also set the ``version`` value in the
``media`` section. The exact string is not important, as long as the value is
identical on every slave, and changed on each upgrade. It is used to make
static file URLs unique, so clients can cache them indefinitely. The IVLE
version is conventionally used as this string.


Getting access to the shared data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We need to mount the shared components of the IVLE data hierarchy from the
master. If you've used the suggested method, follow these instructions.
Otherwise you'll have to work it out for yourself.

First install the NFS common utilities, required for NFS mounts. ::

   sudo apt-get install nfs-common

Now we can add the mount to ``/etc/fstab``. Something like this should do: ::

  themaster:/export/ivle /export/ivle nfs defaults 0 0

Then mount the filesystem, and link the shared directories into the
hierarchy. ::

   mount -a
   ivle-createdatadirs
   rmdir /var/lib/ivle/{sessions,jails}
   ln -s /export/ivle/{sessions,jails} /var/lib/ivle


Configuring Apache
~~~~~~~~~~~~~~~~~~

The slaves use Apache to serve the main IVLE web UI and public user files.
Let's activate the configuration now. ::

   sudo cp /usr/share/doc/ivle/apache.conf /etc/apache2/sites-available/ivle
   sudo a2ensite ivle

Now edit ``/etc/apache2/sites-available/ivle``, and ensure that the
``ServerName`` matches your chosen IVLE web UI domain name, and
``ServerAlias`` your public name. Then reload Apache's configuration. ::

   sudo /etc/init.d/apache2 reload
