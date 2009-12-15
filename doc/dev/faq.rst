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

.. _ref-dev-faq:

**************************
Frequently Asked Questions
**************************

This is a list of Frequently Asked Questions for IVLE developers. It answers
questions about common issues encountered when bludgeoning the system into
behaving.

.. _ref-dev-faq-how:

How can I...
============

.. _ref-dev-faq-config:

... get data out of the IVLE configuration?
-------------------------------------------

::

    from ivle.config import Config
    config = Config()

This makes `config`, a dictionary-tree containing the whole config hierarchy.

For example, to get the Subversion repository path, use
``config['paths']['svn']['repo_path']``.

.. note::
   For code running inside the jail, you will see different configuration
   variables than code running outside. It will be missing a lot of data, and
   will contain some user-specific data.

Database
--------

IVLE exclusively uses the `Storm`_ API for database access. Do not write any
SQL code yourself, or make use of low-level database libraries. The only
exception is in preparing the database schema, which is stored as an SQL file.

.. _Storm: https://storm.canonical.com/

... update the database schema?
-------------------------------

Modify :file:`userdb/users.sql`. Any changes also need to be made in to a
migrations file, in :file:`userdb/migrations/`.

TODO: More detail on migrations.

.. _ref-dev-faq-read-data:

... read data from the database?
--------------------------------

::

    import ivle.database
    # Typically, you import all database classes you want here
    from ivle.database import User

You need a `store` object to perform any interactions with the database. If
you are inside the web app, get a hold of the `req` (request) object, and use
``req.store``. In other code, create a new store as follows (where `config` is
a :ref:`config <ref-dev-faq-config>` object)::

    store = ivle.database.get_store(config)

You can read objects out of the database through the store. For example, to
get a User object::

    user = store.find(User, User.login==username).one()

(Note that ``store.find(User)`` just returns a sequence of all users.)

You can then treat `user` as a normal object, and read from its attributes.
All of the classes are defined in ``ivle/database.py``.

.. note::
   The code must be executed outside of the jail. Jail code runs under user
   privileges and cannot access the database.

.. note::
   For help with the database API, see the `Storm`_ documentation.

... write data to the database?
--------------------------------

Get an object out of the database, as :ref:`above <ref-dev-faq-read-data>`,
and simply write to the object's attributes. This updates the *in-memory* copy
of the data only.

To write the changes back to the database, simply use::

    store.commit()

using the same store object as used to retrieve the object in the first place.

... insert a new object into the database?
------------------------------------------

Create the new object using its constructor, as with any Python object. e.g.::

    import ivle.database
    user = ivle.database.User()

You can then set the attributes of the object as desired. As with writing,
this only creates an *in-memory* object.

To add the object to the database, get a :ref:`store <ref-dev-faq-read-data>`,
and use::

    store.add(user)
    store.commit()

Subversion
----------

... get the local file path to a user's Subversion repo?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get a :ref:`config <ref-dev-faq-config>` object, and use ::

    repopath = os.path.join(config['paths']['svn']['repo_path'],
                            'users', username)

(This should probably be abstracted.)

... get the http:// URL for a user's Subversion repo?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get a :ref:`config <ref-dev-faq-config>` object, and use ::

    repourl = config['urls']['svn_addr'] + '/users/' + username

(This should probably be abstracted.)

... get a Subversion client from Python?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    import ivle.svn
    svnclient = ivle.svn.create_auth_svn_client(username, password)

If you don't have any auth credentials and you just want to do SVN things
which don't require auth (though I don't see why this situation would arise),
you can get an auth-less SVN client, which will raise exceptions if you try to
do authy things (e.g., commit, update or checkout)::

    import pysvn
    svnclient = pysvn.Client()

In either case, the client object will raise `pysvn.ClientError` objects, so
you should be handling those.

You may wish to make error messages simpler using this line::

    svnclient.exception_style = 0

A good example of Subversion client code is in
``ivle/fileservice_lib/action.py``.

.. _ref-dev-faq-where:

Where do I find...
==================

.. This is for finding obscure things in the code.

... the class definitions for database objects?
-----------------------------------------------

All of the classes are defined in ``ivle/database.py``.
