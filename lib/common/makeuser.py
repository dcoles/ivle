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

# TODO: In chown_to_webserver:
# Do not call os.system("chown www-data") - use Python lib
# and use the web server uid given in conf. (Several places).

import md5
import os
import stat
import shutil
import time
import uuid
import warnings
import filecmp
import logging
import conf
import db

def chown_to_webserver(filename):
    """
    Chowns a file so the web server user owns it.
    (This is useful in setting up Subversion conf files).
    Assumes root.
    """
    try:
        os.system("chown -R www-data:www-data %s" % filename)
    except:
        pass

def make_svn_repo(login, throw_on_error=True):
    """Create a repository for the given user.
    """
    path = os.path.join(conf.svn_repo_path, login)
    try:
        res = os.system("svnadmin create '%s'" % path)
        if res != 0 and throw_on_error:
            raise Exception("Cannot create repository for %s" % login)
    except Exception, exc:
        print repr(exc)
        if throw_on_error:
            raise

    chown_to_webserver(path)

def rebuild_svn_config():
    """Build the complete SVN configuration file.
    """
    conn = db.DB()
    res = conn.query("SELECT login, rolenm FROM login;").dictresult()
    groups = {}
    for r in res:
        role = r['rolenm']
        if role not in groups:
            groups[role] = []
        groups[role].append(r['login'])
    f = open(conf.svn_conf + ".new", "w")
    f.write("# IVLE SVN Repositories Configuration\n")
    f.write("# Auto-generated on %s\n" % time.asctime())
    f.write("\n")
    f.write("[groups]\n")
    for (g,ls) in groups.iteritems():
        f.write("%s = %s\n" % (g, ",".join(ls)))
    f.write("\n")
    for r in res:
        login = r['login']
        f.write("[%s:/]\n" % login)
        f.write("%s = rw\n" % login)
        #f.write("@tutor = r\n")
        #f.write("@lecturer = rw\n")
        #f.write("@admin = rw\n")
        f.write("\n")
    f.close()
    os.rename(conf.svn_conf + ".new", conf.svn_conf)
    chown_to_webserver(conf.svn_conf)

def make_svn_config(login, throw_on_error=True):
    """Add an entry to the apache-svn config file for the given user.
       Assumes the given user is either a guest or a student.
    """
    f = open(conf.svn_conf, "a")
    f.write("[%s:/]\n" % login)
    f.write("%s = rw\n" % login)
    #f.write("@tutor = r\n")
    #f.write("@lecturer = rw\n")
    #f.write("@admin = rw\n")
    f.write("\n")
    f.close()
    chown_to_webserver(conf.svn_conf)

def make_svn_auth(login, throw_on_error=True):
    """Setup svn authentication for the given user.
       FIXME: create local.auth entry
    """
    passwd = md5.new(uuid.uuid4().bytes).digest().encode('hex')
    if os.path.exists(conf.svn_auth_ivle):
        create = ""
    else:
        create = "c"

    db.DB().update_user(login, svn_pass=passwd)

    res = os.system("htpasswd -%smb %s %s %s" % (create,
                                              conf.svn_auth_ivle,
                                              login, passwd))
    if res != 0 and throw_on_error:
        raise Exception("Unable to create ivle-auth for %s" % login)

    # Make sure the file is owned by the web server
    if create == "c":
        chown_to_webserver(conf.svn_auth_ivle)

    return passwd

def generate_manifest(basedir, targetdir, parent=''):
    """ From a basedir and a targetdir work out which files are missing or out 
    of date and need to be added/updated and which files are redundant and need 
    to be removed.
    
    parent: This is used for the recursive call to track the relative paths 
    that we have decended.
    """
    
    cmp = filecmp.dircmp(basedir, targetdir)

    # Add all new files and files that have changed
    to_add = [os.path.join(parent,x) for x in (cmp.left_only + cmp.diff_files)]

    # Remove files that are redundant
    to_remove = [os.path.join(parent,x) for x in cmp.right_only]
    
    # Recurse
    for d in cmp.common_dirs:
        newbasedir = os.path.join(basedir, d)
        newtargetdir = os.path.join(targetdir, d)
        newparent = os.path.join(parent, d)
        (sadd,sremove) = generate_manifest(newbasedir, newtargetdir, newparent)
        to_add += sadd
        to_remove += sremove

    return (to_add, to_remove)


def make_jail(username, uid, force=True, svn_pass=None):
    """Creates a new user's jail space, in the jail directory as configured in
    conf.py.

    This only creates things within /home - everything else is expected to be
    part of another UnionFS branch.

    Returns the path to the user's home directory.

    Chowns the user's directory within the jail to the given UID.

    Note: This takes separate username and uid arguments. The UID need not
    *necessarily* correspond to a Unix username at all, if all you are
    planning to do is setuid to it. This allows the caller the freedom of
    deciding the binding between username and uid, if any.

    force: If false, exception if jail already exists for this user.
    If true (default), overwrites it, but preserves home directory.

    svn_pass: If provided this will be a string, the randomly-generated
    Subversion password for this user (if you happen to already have it).
    If not provided, it will be read from the database.
    """
    # MUST run as root or some of this may fail
    if os.getuid() != 0:
        raise Exception("Must run make_jail as root")
    
    # tempdir is for putting backup homes in
    tempdir = os.path.join(conf.jail_base, '__temp__')
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    elif not os.path.isdir(tempdir):
        os.unlink(tempdir)
        os.mkdir(tempdir)
    userdir = os.path.join(conf.jail_src_base, username)
    homedir = os.path.join(userdir, 'home')
    userhomedir = os.path.join(homedir, username)   # Return value

    if os.path.exists(userdir):
        if not force:
            raise Exception("User's jail already exists")
        # User jail already exists. Blow it away but preserve their home
        # directory. It should be all that is there anyway, but you never
        # know!
        # Ignore warnings about the use of tmpnam
        warnings.simplefilter('ignore')
        homebackup = os.tempnam(tempdir)
        warnings.resetwarnings()
        # Note: shutil.move does not behave like "mv" - it does not put a file
        # into a directory if it already exists, just fails. Therefore it is
        # not susceptible to tmpnam symlink attack.
        shutil.move(homedir, homebackup)
        shutil.rmtree(userdir)
        os.makedirs(homedir)
        shutil.move(homebackup, homedir)
    else:
        # No user jail exists
        # Set up the user's home directory
        os.makedirs(userhomedir)
        # Chown (and set the GID to the same as the UID).
        os.chown(userhomedir, uid, uid)
        # Chmod to rwxr-xr-x (755)
        os.chmod(userhomedir, 0755)

    # There is 1 special file which needs to be generated specific to this
    # user: /opt/ivle/lib/conf/conf.py.
    # "__" username "__" users are exempt (special)
    if not (username.startswith("__") and username.endswith("__")):
        make_conf_py(username, userdir, conf.jail_system, svn_pass)

    return userhomedir

def make_conf_py(username, user_jail_dir, staging_dir, svn_pass=None):
    """
    Creates (overwriting any existing file, and creating directories) a
    file /opt/ivle/lib/conf/conf.py in a given user's jail.
    username: Username.
    user_jail_dir: User's jail dir, ie. conf.jail_base + username
    staging_dir: The dir with the staging copy of the jail. (With the
        template conf.py file).
    svn_pass: As with make_jail. User's SVN password, but if not supplied,
        will look up in the DB.
    """
    template_conf_path = os.path.join(staging_dir,"opt/ivle/lib/conf/conf.py")
    conf_path = os.path.join(user_jail_dir, "opt/ivle/lib/conf/conf.py")
    os.makedirs(os.path.dirname(conf_path))

    # If svn_pass isn't supplied, grab it from the DB
    if svn_pass is None:
        dbconn = db.DB()
        svn_pass = dbconn.get_user(username).svn_pass
        dbconn.close()

    # Read the contents of the template conf file
    try:
        template_conf_file = open(template_conf_path, "r")
        template_conf_data = template_conf_file.read()
        template_conf_file.close()
    except:
        # Couldn't open template conf.py for some reason
        # Just treat it as empty file
        template_conf_data = ("# Warning: Problem building config script.\n"
                              "# Could not find template conf.py file.\n")

    conf_file = open(conf_path, "w")
    conf_file.write(template_conf_data)
    conf_file.write("\n# The login name for the owner of the jail\n")
    conf_file.write("login = %s\n" % repr(username))
    conf_file.write("\n")
    conf_file.write("# The subversion-only password for the owner of "
        "the jail\n")
    conf_file.write("svn_pass = %s\n" % repr(svn_pass))
    conf_file.close()

    # Make this file world-readable
    # (chmod 644 conf_path)
    os.chmod(conf_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP
                        | stat.S_IROTH)

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

def make_user_db(throw_on_error = True, **kwargs):
    """Creates a user's entry in the database, filling in all the fields.
    All arguments must be keyword args. They are the fields in the table.
    However, instead of supplying a "passhash", you must supply a
    "password" argument, which will be hashed internally.
    Also do not supply a state. All users are created in the "no_agreement"
    state.
    Throws an exception if the user already exists.
    """
    dbconn = db.DB()
    dbconn.create_user(**kwargs)
    dbconn.close()

    if kwargs['password']:
        if os.path.exists(conf.svn_auth_local):
            create = ""
        else:
            create = "c"
        res = os.system("htpasswd -%smb %s %s %s" % (create,
                                                     conf.svn_auth_local,
                                                     kwargs['login'],
                                                     kwargs['password']))
        if res != 0 and throw_on_error:
            raise Exception("Unable to create local-auth for %s" % kwargs['login'])

    # Make sure the file is owned by the web server
    if create == "c":
        chown_to_webserver(conf.svn_auth_local)

def mount_jail(login):
    # This is where we'll mount to...
    destdir = os.path.join(conf.jail_base, login)
    # ... and this is where we'll get the user bits.
    srcdir = os.path.join(conf.jail_src_base, login)
    try:
        if not os.path.exists(destdir):
            os.mkdir(destdir)
        if os.system('/bin/mount -t aufs -o dirs=%s:%s=ro none %s'
                     % (srcdir, conf.jail_system, destdir)) == 0:
            logging.info("mounted user %s's jail." % login)
        else:
            logging.error("failed to mount user %s's jail!" % login)
    except Exception, message:
        logging.warning(str(message))
