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

*************
Coding Policy
*************

Code Style
==========
IVLE is mostly written in the Python programming language. As such, code 
should follow the standards set forward in :pep:`8`. It is particularly 
important that code uses a uniform indentation style otherwise this may cause 
unusual behavior or make the code difficult to understand. This means that 
code should be written with 4 spaces per indent and not use any tabs for 
indentation.

IVLE also includes a modest quantity of code written in other languages such 
as JavaScript, HTML and C. In languages that use braces to delimit code blocks 
the Allman style of indentation is used::

    while (x == y)
    {
        something();
        somethingelse();
    }
    finalthing();

If in doubt, follow the existing coding style used in the module. Having a 
consistent coding style is often of far greater value than choosing any one 
style over another.

Version Control
===============
Code is developed on `Launchpad <https://launchpad.net/>`_ using the `Bazaar 
<http://bazaar-vcs.org/>`_ version control system. The main branch for 
development ``lp:ivle``, though more complex features or large changes should 
be developed in a separate branch with the name
:samp:`lp:~ivle-dev/ivle/{branch-name}` and then merged into the trunk when 
complete.

All associated branches can be found on the `IVLE Launchpad Project Page 
<https://launchpad.net/ivle/>`_.

Licence
=======
IVLE is licenced under the `GNU General Public License Version 2.0 
<http://www.gnu.org/licenses/gpl-2.0.html>`_ and requires that all 
contributions be made under it or a compatible license. Code contributions 
should also contain a header of the following form::

    # IVLE - Informatics Virtual Learning Environment
    # Copyright (C) 2007-2009 The University of Melbourne
    #
    # This program is free software; you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation; either version 2 of the License, or
    # (at your option) any later version.
    #
    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.
    #
    # You should have received a copy of the GNU General Public License
    # along with this program; if not, write to the Free Software
    # Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


