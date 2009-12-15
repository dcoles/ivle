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
