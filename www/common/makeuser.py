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
# Date:   1/2/2008

# Allows creation of users. This sets up the following:
# * User's jail and home directory within the jail.
# * Subversion repository (TODO)
# * Check out Subversion workspace into jail (TODO)
# * Database details for user
# * Unix user account

# TODO: Sanitize login name and other fields.

import os
import shutil

import conf
import db

def makeuser(username, password, nick, fullname, rolenm, studentid):
    """Creates a new user on a pre-installed system.
    Sets up the following:
    * User's jail and home directory within the jail.
    * Subversion repository
    * Check out Subversion workspace into jail
    * Database details for user
    * Unix user account
    """
    homedir = make_jail(username)
    make_user_db(username, password, nick, fullname, rolenm, studentid)
    # TODO: -p password (need to use crypt)
    if os.system("useradd -d %s '%s'" % (homedir, username)) != 0:
        raise Exception("Failed to add Unix user account")

def make_jail(username):
    """Creates a new user's jail space, in the jail directory as configured in
    conf.py.

    This expects there to be a "template" directory within the jail root which
    contains all the files for a sample student jail. It creates the student's
    directory in the jail root, by making a hard-link copy of every file in the
    template directory, recursively.

    Returns the path to the user's home directory.
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
    homedir = os.path.join(userdir, 'home', username)
    os.mkdir(homedir)
    return homedir

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

def make_user_db(login, password, nick, fullname, rolenm, studentid):
    """Creates a user's entry in the database, filling in all the fields."""
    dbconn = db.DB()
    dbconn.create_user(login, password, nick, fullname, rolenm, studentid)
    dbconn.close()
