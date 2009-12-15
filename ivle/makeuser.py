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

"""User and group filesystem management helpers."""

import hashlib
import os
import stat
import shutil
import time
import uuid
import warnings
import logging
import subprocess

from storm.expr import Select, Max

import ivle.config
from ivle.database import (User, ProjectGroup, Assessed, ProjectSubmission,
        Project, ProjectSet, Offering, Enrolment, Subject, Semester)

def chown_to_webserver(filename):
    """chown a directory and its contents to the web server.

    Recursively chowns a file or directory so the web server user owns it.
    Assumes root.
    """
    subprocess.call(['chown', '-R', 'www-data:www-data', filename])

def make_svn_repo(path, throw_on_error=True):
    """Create a Subversion repository at the given path."""
    try:
        res = subprocess.call(['svnadmin', 'create', path])
        if res != 0 and throw_on_error:
            raise Exception("Cannot create repository: %s" % path)
    except Exception, exc:
        print repr(exc)
        if throw_on_error:
            raise

    chown_to_webserver(path)

def rebuild_svn_config(store, config):
    """Build the complete SVN configuration file.

    @param config: An ivle.config.Config object.
    """
    users = store.find(User)
    conf_name = config['paths']['svn']['conf']
    temp_name = conf_name + ".new"
    f = open(temp_name, "w")
    f.write("""\
# IVLE SVN repository authorisation configuration
# Generated: %(time)s
""" % {'time': time.asctime()})

    for u in users:
        f.write("""
[%(login)s:/]
%(login)s = rw
""" % {'login': u.login})

    # Now we need to grant offering tutors and lecturers access to the latest
    # submissions in their offerings. There are much prettier ways to do this,
    # but a lot of browser requests call this function, so it needs to be
    # fast. We can grab all of the paths needing authorisation directives with
    # a single query, and we cache the list of viewers for each offering.
    offering_viewers_cache = {}
    for (login, psid, pspath, offeringid) in store.find(
        (User.login, ProjectSubmission.id, ProjectSubmission.path,
         Offering.id),
            Assessed.id == ProjectSubmission.assessed_id,
            User.id == Assessed.user_id,
            Project.id == Assessed.project_id,
            ProjectSet.id == Project.project_set_id,
            Offering.id == ProjectSet.id,
            ProjectSubmission.date_submitted == Select(
                    Max(ProjectSubmission.date_submitted),
                    ProjectSubmission.assessed_id == Assessed.id,
                    tables=ProjectSubmission
            )
        ):

        # Do we already have the list of logins authorised for this offering
        # cached? If not, get it.
        if offeringid not in offering_viewers_cache:
            offering_viewers_cache[offeringid] = list(store.find(
                    User.login,
                    User.id == Enrolment.user_id,
                    Enrolment.offering_id == offeringid,
                    Enrolment.role.is_in((u'tutor', u'lecturer'))
                )
            )

        f.write("""
# Submission %(id)d
[%(login)s:%(path)s]
""" % {'login': login, 'id': psid, 'path': pspath})

        for viewer_login in offering_viewers_cache[offeringid]:
            # We don't want to override the owner's write privilege,
            # so we don't add them to the read-only ACL.
            if login != viewer_login:
                f.write("%s = r\n" % viewer_login)

    f.close()
    os.rename(temp_name, conf_name)
    chown_to_webserver(conf_name)

def rebuild_svn_group_config(store, config):
    """Build the complete SVN configuration file for groups

    @param config: An ivle.config.Config object.
    """
    conf_name = config['paths']['svn']['group_conf']
    temp_name = conf_name + ".new"
    f = open(temp_name, "w")

    f.write("""\
# IVLE SVN group repository authorisation configuration
# Generated: %(time)s

""" % {'time': time.asctime()})

    group_members_cache = {}
    for group in store.find(ProjectGroup):
        offering = group.project_set.offering
        reponame = "_".join([offering.subject.short_name,
                             offering.semester.year,
                             offering.semester.semester,
                             group.name])

        f.write("[%s:/]\n" % reponame)
        if group.id not in group_members_cache:
            group_members_cache[group.id] = set()
        for user in group.members:
            group_members_cache[group.id].add(user.login)
            f.write("%s = rw\n" % user.login)
        f.write("\n")

    # Now we need to grant offering tutors and lecturers access to the latest
    # submissions in their offerings. There are much prettier ways to do this,
    # but a lot of browser requests call this function, so it needs to be
    # fast. We can grab all of the paths needing authorisation directives with
    # a single query, and we cache the list of viewers for each offering.
    offering_viewers_cache = {}
    for (ssn, year, sem, name, psid, pspath, gid, offeringid) in store.find(
        (Subject.short_name, Semester.year, Semester.semester,
         ProjectGroup.name, ProjectSubmission.id, ProjectSubmission.path,
         ProjectGroup.id, Offering.id),
            Assessed.id == ProjectSubmission.assessed_id,
            ProjectGroup.id == Assessed.project_group_id,
            Project.id == Assessed.project_id,
            ProjectSet.id == Project.project_set_id,
            Offering.id == ProjectSet.offering_id,
            Subject.id == Offering.subject_id,
            Semester.id == Offering.semester_id,
            ProjectSubmission.date_submitted == Select(
                    Max(ProjectSubmission.date_submitted),
                    ProjectSubmission.assessed_id == Assessed.id,
                    tables=ProjectSubmission
            )
        ):

        reponame = "_".join([ssn, year, sem, name])

        # Do we already have the list of logins authorised for this offering
        # cached? If not, get it.
        if offeringid not in offering_viewers_cache:
            offering_viewers_cache[offeringid] = list(store.find(
                    User.login,
                    User.id == Enrolment.user_id,
                    Enrolment.offering_id == offeringid,
                    Enrolment.role.is_in((u'tutor', u'lecturer'))
                )
            )

        f.write("""
# Submission %(id)d
[%(repo)s:%(path)s]
""" % {'repo': reponame, 'id': psid, 'path': pspath})

        for viewer_login in offering_viewers_cache[offeringid]:
            # Skip existing group members, or they can't write to it any more.
            if viewer_login not in group_members_cache[gid]:
                f.write("%s = r\n" % viewer_login)

    f.close()
    os.rename(temp_name, conf_name)
    chown_to_webserver(conf_name)

def make_svn_auth(store, login, config, throw_on_error=True):
    """Create a Subversion password for a user.

    Generates a new random Subversion password, and assigns it to the user.
    The password is added to Apache's Subversion authentication file.
    """
    # filename is, eg, /var/lib/ivle/svn/ivle.auth
    filename = config['paths']['svn']['auth_ivle']
    if os.path.exists(filename):
        create = ""
    else:
        create = "c"

    user = User.get_by_login(store, login)

    if user.svn_pass is None:
        passwd = hashlib.md5(uuid.uuid4().bytes).hexdigest()
        user.svn_pass = unicode(passwd)

    res = subprocess.call(['htpasswd', '-%smb' % create,
                           filename, login, user.svn_pass])
    if res != 0 and throw_on_error:
        raise Exception("Unable to create ivle-auth for %s" % login)

    # Make sure the file is owned by the web server
    if create == "c":
        chown_to_webserver(filename)

    return user.svn_pass

def make_jail(user, config, force=True):
    """Create or update a user's jail.

    Only the user-specific parts of the jail are created here - everything
    else is expected to be part of another aufs branch.

    Returns the path to the user's home directory.

    Chowns the user's directory within the jail to the given UID.

    @param force: If False, raise an exception if the user already has a jail.
                  If True (default), rebuild the jail preserving /home.
    """
    # MUST run as root or some of this may fail
    if os.getuid() != 0:
        raise Exception("Must run make_jail as root")
    
    # tempdir is for putting backup homes in
    jail_src_base = config['paths']['jails']['src']
    tempdir = os.path.join(jail_src_base, '__temp__')
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    elif not os.path.isdir(tempdir):
        os.unlink(tempdir)
        os.mkdir(tempdir)
    userdir = os.path.join(jail_src_base, user.login)
    homedir = os.path.join(userdir, 'home')
    tmpdir = os.path.join(userdir, 'tmp')
    userhomedir = os.path.join(homedir, user.login)   # Return value

    if os.path.exists(userdir):
        if not force:
            raise Exception("User's jail already exists")
        # User jail already exists. Blow it away but preserve their home
        # directory. It should be all that is there anyway, but you never
        # know!
        # Ignore warnings about the use of tempnam
        warnings.simplefilter('ignore')
        homebackup = os.tempnam(tempdir)
        warnings.resetwarnings()
        # Back up the /home directory, delete the entire jail, recreate the
        # jail directory tree, then copy the /home back
        # NOTE that shutil.move changed in Python 2.6, it now moves a
        # directory INTO the target (like `mv`), which it didn't use to do.
        # This code works regardless.
        shutil.move(userhomedir, homebackup)
        shutil.rmtree(userdir)
        os.makedirs(homedir)
        shutil.move(homebackup, userhomedir)
        # Change the ownership of all the files to the right unixid
        logging.debug("chown %s's home directory files to uid %d"
            %(user.login, user.unixid))
        os.spawnvp(os.P_WAIT, 'chown', ['chown', '-R', '%d:%d' % (user.unixid,
                                        user.unixid), userhomedir])
    else:
        # No user jail exists
        # Set up the user's home directory
        os.makedirs(userhomedir)
        # Chown (and set the GID to the same as the UID).
        os.chown(userhomedir, user.unixid, user.unixid)
        # Chmod to rwxr-xr-x (755)
        os.chmod(userhomedir, 0755)

    make_ivle_conf(user.login, userdir, user.svn_pass, config)
    make_etc_passwd(user.login, userdir, config['paths']['jails']['template'],
                    user.unixid)
    os.makedirs(tmpdir)
    os.chmod(tmpdir, 01777)

    return userhomedir

def make_ivle_conf(username, user_jail_dir, svn_pass, sys_config):
    """Generate an ivle.conf for a user's jail.

    Creates (overwriting any existing file, and creating directories) a
    file /etc/ivle/ivle.conf in a given user's jail.

    @param username: Username.
    @param user_jail_dir: User's jail dir, ie. ['jails']['src'] + username
    @param svn_pass: User's SVN password.
    @param sys_config: An ivle.config.Config object (the system-wide config).
    """
    conf_path = os.path.join(user_jail_dir, "home/.ivle.conf")
    if not os.path.exists(os.path.dirname(conf_path)):
        os.makedirs(os.path.dirname(conf_path))

    # In the "in-jail" version of conf, we don't need MOST of the details
    # (it would be a security risk to have them here).
    # So we just write root_dir.
    conf_obj = ivle.config.Config(blank=True)
    conf_obj.filename = conf_path
    conf_obj['urls']['root'] = sys_config['urls']['root']
    conf_obj['urls']['public_host'] = sys_config['urls']['public_host']
    conf_obj['urls']['svn_addr'] = sys_config['urls']['svn_addr']
    conf_obj['user_info']['login'] = username
    conf_obj['user_info']['svn_pass'] = svn_pass
    conf_obj.write()

    # Make this file world-readable
    # (chmod 644 conf_path)
    os.chmod(conf_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP
                        | stat.S_IROTH)

def make_etc_passwd(username, user_jail_dir, template_dir, unixid):
    """Create a passwd file for a user's jail.

    Creates /etc/passwd in the given user's jail. This will be identical to
    that in the template jail, except for the added entry for this user.
    """
    template_passwd_path = os.path.join(template_dir, "home/.passwd")
    passwd_path = os.path.join(user_jail_dir, "home/.passwd")
    passwd_dir = os.path.dirname(passwd_path)
    if not os.path.exists(passwd_dir):
        os.makedirs(passwd_dir)
    shutil.copy(template_passwd_path, passwd_path)
    passwd_file = open(passwd_path, 'a')
    passwd_file.write('%s:x:%d:%d::/home/%s:/bin/bash'
                      % (username, unixid, unixid, username))
    passwd_file.close()
