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
import ivle.conf
import ivle.pulldown_subj

from ivle.database import ProjectGroup

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

def make_svn_repo(path, throw_on_error=True):
    """Create a Subversion repository at the given path.
    """
    try:
        res = os.system("svnadmin create '%s'" % path)
        if res != 0 and throw_on_error:
            raise Exception("Cannot create repository: %s" % path)
    except Exception, exc:
        print repr(exc)
        if throw_on_error:
            raise

    chown_to_webserver(path)

def rebuild_svn_config(store):
    """Build the complete SVN configuration file.
    """
    users = store.find(ivle.database.User)
    groups = {}
    # TODO: Populate groups with per-offering tutors/lecturers/etc.
    f = open(ivle.conf.svn_conf + ".new", "w")
    f.write("# IVLE SVN Repositories Configuration\n")
    f.write("# Auto-generated on %s\n" % time.asctime())
    f.write("\n")
    f.write("[groups]\n")
    for (g,ls) in groups.iteritems():
        f.write("%s = %s\n" % (g, ",".join(ls)))
    f.write("\n")
    for u in users:
        f.write("[%s:/]\n" % u.login)
        f.write("%s = rw\n" % u.login)
        #f.write("@tutor = r\n")
        #f.write("@lecturer = rw\n")
        #f.write("@admin = rw\n")
        f.write("\n")
    f.close()
    os.rename(ivle.conf.svn_conf + ".new", ivle.conf.svn_conf)
    chown_to_webserver(ivle.conf.svn_conf)

def rebuild_svn_group_config(store):
    """Build the complete SVN configuration file for groups
    """
    f = open(ivle.conf.svn_group_conf + ".new", "w")
    f.write("# IVLE SVN Group Repositories Configuration\n")
    f.write("# Auto-generated on %s\n" % time.asctime())
    f.write("\n")
    for group in store.find(ProjectGroup):
        offering = group.project_set.offering
        reponame = "_".join([offering.subject.short_name,
                             offering.semester.year,
                             offering.semester.semester,
                             group.name])
        f.write("[%s:/]\n"%reponame)
        for user in group.members:
            f.write("%s = rw\n" % user.login)
        f.write("\n")
    f.close()
    os.rename(ivle.conf.svn_group_conf + ".new", ivle.conf.svn_group_conf)
    chown_to_webserver(ivle.conf.svn_group_conf)

def make_svn_auth(store, login, throw_on_error=True):
    """Setup svn authentication for the given user.
       Uses the given DB store object. Does not commit to the db.
    """
    passwd = md5.new(uuid.uuid4().bytes).digest().encode('hex')
    if os.path.exists(ivle.conf.svn_auth_ivle):
        create = ""
    else:
        create = "c"

    user = ivle.database.User.get_by_login(store, login)
    user.svn_pass = unicode(passwd)

    res = os.system("htpasswd -%smb %s %s %s" % (create,
                                              ivle.conf.svn_auth_ivle,
                                              login, passwd))
    if res != 0 and throw_on_error:
        raise Exception("Unable to create ivle-auth for %s" % login)

    # Make sure the file is owned by the web server
    if create == "c":
        chown_to_webserver(ivle.conf.svn_auth_ivle)

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


def make_jail(user, force=True):
    """Creates a new user's jail space, in the jail directory as configured in
    conf.py.

    This only creates things within /home - everything else is expected to be
    part of another UnionFS branch.

    Returns the path to the user's home directory.

    Chowns the user's directory within the jail to the given UID.

    force: If false, exception if jail already exists for this user.
    If true (default), overwrites it, but preserves home directory.
    """
    # MUST run as root or some of this may fail
    if os.getuid() != 0:
        raise Exception("Must run make_jail as root")
    
    # tempdir is for putting backup homes in
    tempdir = os.path.join(ivle.conf.jail_base, '__temp__')
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    elif not os.path.isdir(tempdir):
        os.unlink(tempdir)
        os.mkdir(tempdir)
    userdir = os.path.join(ivle.conf.jail_src_base, user.login)
    homedir = os.path.join(userdir, 'home')
    userhomedir = os.path.join(homedir, user.login)   # Return value

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
        # Change the ownership of all the files to the right unixid
        logging.debug("chown %s's home directory files to uid %d"
            %(user.login, user.unixid))
        os.chown(userhomedir, user.unixid, user.unixid)
        for root, dirs, files in os.walk(userhomedir):
            for fsobj in dirs + files:
                os.chown(os.path.join(root, fsobj), user.unixid, user.unixid)
    else:
        # No user jail exists
        # Set up the user's home directory
        os.makedirs(userhomedir)
        # Chown (and set the GID to the same as the UID).
        os.chown(userhomedir, user.unixid, user.unixid)
        # Chmod to rwxr-xr-x (755)
        os.chmod(userhomedir, 0755)

    make_conf_py(user.login, userdir, user.svn_pass)
    make_etc_passwd(user.login, userdir, ivle.conf.jail_system, user.unixid)

    return userhomedir

def make_conf_py(username, user_jail_dir, svn_pass):
    """
    Creates (overwriting any existing file, and creating directories) a
    file ${python_site_packages}/ivle/conf/conf.py in a given user's jail.
    username: Username.
    user_jail_dir: User's jail dir, ie. ivle.conf.jail_base + username
    svn_pass: User's SVN password.
    """
    conf_path = os.path.join(user_jail_dir,
            ivle.conf.python_site_packages[1:], "ivle/conf/conf.py")
    os.makedirs(os.path.dirname(conf_path))

    # In the "in-jail" version of conf, we don't need MOST of the details
    # (it would be a security risk to have them here).
    # So we just write root_dir, and jail_base is "/".
    # (jail_base being "/" means "jail-relative" paths are relative to "/"
    # when inside the jail.)

    # XXX: jail_base is wrong and shouldn't be here. Unfortunately, jail code
    #      uses ivle.studpath.url_to_{local,jailpaths}, both of which use
    #      jail_base. Note that they don't use the bits of the return value
    #      that depend on jail_base, so it can be any string.
    conf_file = open(conf_path, "w")
    conf_file.write("""# IVLE jail configuration

# In URL space, where in the site is IVLE located. (All URLs will be prefixed
# with this).
# eg. "/" or "/ivle".
root_dir = %(root_dir)r

# This value is not relevant inside the jail, but must remain for now. See
# the XXX in ivle.makeuser.make_conf_py.
jail_base = '/'

# The hostname for serving publicly accessible pages
public_host = %(public_host)r

# The URL under which the Subversion repositories are located.
svn_addr = %(svn_addr)r

# The login name for the owner of the jail
login = %(username)r

# The subversion-only password for the owner of the jail
svn_pass = %(svn_pass)r
""" % {'root_dir': ivle.conf.root_dir,
       'public_host': ivle.conf.public_host,
       'svn_addr': ivle.conf.svn_addr,
       'username': username,
       'svn_pass': svn_pass,
      })
    conf_file.close()

    # Make this file world-readable
    # (chmod 644 conf_path)
    os.chmod(conf_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP
                        | stat.S_IROTH)

def make_etc_passwd(username, user_jail_dir, template_dir, unixid):
    """
    Creates /etc/passwd in the given user's jail. This will be identical to
    that in the template jail, except for the added entry for this user.
    """
    template_passwd_path = os.path.join(template_dir, "etc/passwd")
    passwd_path = os.path.join(user_jail_dir, "etc/passwd")
    passwd_dir = os.path.dirname(passwd_path)
    if not os.path.exists(passwd_dir):
        os.makedirs(passwd_dir)
    shutil.copy(template_passwd_path, passwd_path)
    passwd_file = open(passwd_path, 'a')
    passwd_file.write('%s:x:%d:%d::/home/%s:/bin/bash'
                      % (username, unixid, unixid, username))
    passwd_file.close()

def mount_jail(login):
    # This is where we'll mount to...
    destdir = os.path.join(ivle.conf.jail_base, login)
    # ... and this is where we'll get the user bits.
    srcdir = os.path.join(ivle.conf.jail_src_base, login)
    try:
        if not os.path.exists(destdir):
            os.mkdir(destdir)
        if os.system('/bin/mount -t aufs -o dirs=%s:%s=ro none %s'
                     % (srcdir, ivle.conf.jail_system, destdir)) == 0:
            logging.info("mounted user %s's jail." % login)
        else:
            logging.error("failed to mount user %s's jail!" % login)
    except Exception, message:
        logging.warning(str(message))
