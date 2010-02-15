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

********************
Documentation Policy
********************

The IVLE docs are written entirely in `Sphinx`_, with the exception of user
docs. Documentation is divided into three sections, by target audience:

* User documentation is currently maintained as raw HTML files in individual
  files within the source tree. For example, the "Browser" help page is
  located at ``/ivle/webapp/filesystem/browser/help.html``. These files do not
  have an HTML header; their outer element should be ``<div
  class="helpfile">``.
* Advanced users and system administrators documentation, called "The IVLE
  Manual", located within the source tree at ``/doc/man``. This section should
  not describe any of the code or system architecture, except as visible to
  the system administrator.
* Developer documentation, located within the source tree at ``/doc/dev``.
  This should describe the architecture and workings of the system, but not
  document specific functions (that should be done as docstrings in the Python
  code).

.. _Sphinx: http://sphinx.pocoo.org/

Sphinx documentation style
==========================

Headings
--------

reStructuredText allows arbitrary heading styles. Use the following heading
styles::

 *********
 Heading 1
 *********

 Heading 2
 =========

 Heading 3
 ---------

 Heading 4
 ~~~~~~~~~

Cross-referencing
-----------------

As much as possible, use `semantic markup`_. For example, when describing a
command-line option, use ``:option:`optname``` rather than ````optname````.
This is more semantic, prettier, and generates links where possible.

Links
-----

External links should be written in the form ```http://example.com`_`` or
```Example <http://example.com>`_``. Better yet, use the name only in quotes,
such as ```Example`_``, and at the end of the section, include the reference,
like this::

 .. _Example: http://example.com

Internal links *should* be written in the form ``:ref:`ref-section-name```.
Note that the form ```ref-section-name`_`` is also valid, but has some
significant drawbacks:

* It doesn't work across files,
* On a broken link, it will just link to a page called ``ref-section-name``,
  rather than producing a Sphinx compile-time error.

Therefore, **always** use the ``:ref:`` notation for internal links.

When cross-referencing a section label, place the label above the section
heading, with one blank line in between the label and heading, like this::

 .. _section-name:

 Section Heading
 ===============

.. _semantic markup: http://sphinx.pocoo.org/markup/inline.html

Publishing documentation to the website
=======================================

We currently publish documentation to our old Google Code Subversion
repository, so they can be linked to from the website. This is done with the
``ivle-push-docs-to-gc`` script in ``lp:~ivle-dev/ivle/dev-scripts``. See
the comments at the top of that file for instructions.
