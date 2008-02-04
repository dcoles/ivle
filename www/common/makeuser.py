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
# Users must not be called "temp" or "template".

# TODO: When creating a new home directory, chown it to its owner

import os
import shutil
import warnings

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

def make_jail(username, force=True):
    """Creates a new user's jail space, in the jail directory as configured in
    conf.py.

    This expects there to be a "template" directory within the jail root which
    contains all the files for a sample student jail. It creates the student's
    directory in the jail root, by making a hard-link copy of every file in the
    template directory, recursively.

    Returns the path to the user's home directory.

    force: If false, exception if jail already exists for this user.
    If true (default), overwrites it, but preserves home directory.
    """
    # MUST run as root or some of this may fail
    if os.getuid() != 0:
        raise Exception("Must run make_jail as root")
    
    templatedir = os.path.join(conf.jail_base, 'template')
    if not os.path.isdir(templatedir):
        raise Exception("Template jail directory does not exist: " +
            templatedir)
    # tempdir is for putting backup homes in
    tempdir = os.path.join(conf.jail_base, 'temp')
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    elif not os.path.isdir(tempdir):
        os.unlink(tempdir)
        os.mkdir(tempdir)
    userdir = os.path.join(conf.jail_base, username)
    homedir = os.path.join(userdir, 'home')

    if os.path.exists(userdir):
        if not force:
            raise Exception("User's jail already exists")
        # User jail already exists. Blow it away but preserve their home
        # directory.
        # Ignore warnings about the use of tmpnam
        warnings.simplefilter('ignore')
        homebackup = os.tempnam(tempdir)
        warnings.resetwarnings()
        # Note: shutil.move does not behave like "mv" - it does not put a file
        # into a directory if it already exists, just fails. Therefore it is
        # not susceptible to tmpnam symlink attack.
        shutil.move(homedir, homebackup)
        try:
            # Any errors that occur after making the backup will be caught and
            # the backup will be un-made.
            # XXX This will still leave the user's jail in an unusable state,
            # but at least they won't lose their files.
            shutil.rmtree(userdir)

            # Hard-link (copy aliasing) the entire tree over
            linktree(templatedir, userdir)
        finally:
            # Set up the user's home directory (restore backup)
            # First make sure the directory is empty and its parent exists
            try:
                shutil.rmtree(homedir)
            except:
                pass
            # XXX If this fails the user's directory will be lost (in the temp
            # directory). But it shouldn't fail as homedir should not exist.
            os.makedirs(homedir)
            shutil.move(homebackup, homedir)
        return os.path.join(homedir, username)
    else:
        # No user jail exists
        # Hard-link (copy aliasing) the entire tree over
        linktree(templatedir, userdir)

        # Set up the user's home directory
        userhomedir = os.path.join(homedir, username)
        os.mkdir(userhomedir)
        return userhomedir

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

def make_user_db(login, password, nick, fullname, rolenm, studentid,
    force=True):
    """Creates a user's entry in the database, filling in all the fields.
    If force is False, throws an exception if the user already exists.
    If True, overwrites the user's entry in the DB.
    """
    dbconn = db.DB()
    if force:
        # Delete user if it exists
        try:
            dbconn.delete_user(login)
        except:
            pass
    dbconn.create_user(login, password, nick, fullname, rolenm, studentid)
    dbconn.close()
