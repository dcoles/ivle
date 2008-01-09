# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2008 The University of Melbourne
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

# Module: MakeUser
# Author: Matt Giuca
# Date:   9/1/2008

# Allows creation of users. This sets up the user's jail and home directory
# within the jail.

import os
import shutil

import conf

def makeuser(username):
    """Creates a new user's jail space, in the jail directory as configured in
    conf.py.

    This expects there to be a "template" directory within the jail root which
    contains all the files for a sample student jail. It creates the student's
    directory in the jail root, by making a hard-link copy of every file in the
    template directory, recursively.
    """
    templatedir = os.path.join(conf.jail_base, 'template')
    if not os.path.isdir(templatedir):
        raise Exception("Template jail directory does not exist: " +
            templatedir)
    userdir = os.path.join(conf.jail_base, username)
    if os.path.exists(userdir):
        raise Exception("User's jail directory already exists: " +
            userdir)

    # Hard-link (copy aliasing) the entire tree over
    linktree(templatedir, userdir)

    # Set up the user's home directory
    os.mkdir(os.path.join(userdir, 'home', username))

def linktree(src, dst):
    """Recursively hard-link a directory tree using os.link().

    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    Symlinks are preserved (in fact, hard links are created which point to the
    symlinks).

    Code heavily based upon shutil.copytree from Python 2.5 library.
    """
    names = os.listdir(src)
    os.makedirs(dst)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.isdir(srcname):
                linktree(srcname, dstname)
            else:
                os.link(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error), why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Exception, err:
            errors.append(err.args[0])
    try:
        shutil.copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError, why:
        errors.extend((src, dst, str(why)))
    if errors:
        raise Exception, errors
