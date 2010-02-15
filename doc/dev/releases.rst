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

********
Releases
********

To release IVLE, both generic source tarballs and Ubuntu packages should
be published.


Tag the release in Bazaar
=========================

To note down the release's revision in the Bazaar trunk, run ``bzr tag
-d lp:ivle VERSION``.


Generate a source tarball
=========================

To generate a tarball of the current state of trunk, run ``bzr export 
ivle-VERSION.tar.gz lp:ivle``.


Release it on Launchpad
=======================

As a member of the `IVLE Developers <https://launchpad.net/~ivle-dev>`_ team,
visit the `IVLE project page <https://launchpad.net/ivle>`_. There you'll see
a graph of IVLE's series, milestones and releases.

Clicking on the series in which this release should be created will present
a list of existing milestones and releases. If a milestone for this release
already exists, click "Release now". If not, click "Create release". Enter
the release date on the following form, and confirm the creation.

To upload the release tarball for the world to see, hit "Add download file" on
the release page. Give a meaningful description like "IVLE 1.0 source", select
the file, and ensure that the type is "Code Release Tarball".


.. seealso::

   `Launchpad release documentation <https://help.launchpad.net/Projects/SeriesMilestonesReleases>`_
      All you could ever want to know about Launchpad's series, milestones and
      releases model.


Publish an Ubuntu package
=========================

An Ubuntu package is kept in the `PPA for production environments
<https://launchpad.net/~unimelb-ivle/+archive/production>`_. Releases should
be pushed out to there if destined for production systems. The packaging is
kept in a separate branch: `lp:~ivle-dev/ivle/debian-packaging
<https://code.launchpad.net/~ivle-dev/ivle/debian-packaging>`_.

You will need to be a member of the `University of Melbourne IVLE developers
<https://launchpad.net/~unimelb-ivle>`_ team, have an OpenPGP key assigned to
your account, and have signed the Ubuntu Code of Conduct. See the PPA
documentation linked below for instructions. You should be able to build
the package on any Debian-derived operating system that uses ``dpkg``.
You also need to have an SSH key `associated with your account
<https://help.launchpad.net/YourAccount/CreatingAnSSHKeyPair>`_ so you can
commit to the branch on Launchpad.

When performing a release, you should merge trunk into a checkout of the
packaging branch. Then run ``dch -i`` to add a new Debian changelog entry.
For the Debian version string, append ``-0ppa1`` to the IVLE version (eg.
``1.0-0ppa1``). Make sure that you target to the correct Ubuntu series
(currently ``hardy``). Also ensure that your name and email address are set
correctly at the bottom of the new entry.

Next ensure that you have a copy of the release tarball in the parent
directory, named ``ivle_VERSION.orig.tar.gz``. Once that's there, run
``debuild -S -sa -i`` to build the source package and have the results placed
in the parent directory.

``dput ppa:unimelb-ivle/production ivle_VERSION_source.changes`` will now
upload the package to the production PPA. You should receive an acknowledgement
email from Launchpad within five minutes, at which point Launchpad will begin
building binaries from the source package. You can check the build progress
on the `PPA detail page
<https://launchpad.net/~unimelb-ivle/+archive/production/+packages>`_.

Remember to commit to and push the ``debian-packaging`` branch when done.

.. seealso::

   `Launchpad PPA documentation <https://help.launchpad.net/Packaging/PPA>`_
      All you could ever want to know about using Launchpad's PPA
      functionality.

   `Ubuntu Packaging Guide <https://wiki.ubuntu.com/PackagingGuide/Basic>`_
      All you could ever want to know about Ubuntu packaging.
