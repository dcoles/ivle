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

# Module: setup/util
# Author: Matt Giuca, Refactored by David Coles
# Date:   02/07/2008

# setup/util.py
# Contains a set of functions useful for the setup program.

import os
import shutil
import errno
import sys
import string
import stat
import optparse
import mimetypes

__all__ = ['PYTHON_VERSION', 'copy_file_to_jail', 'RunError',
           'action_runprog', 'action_remove', 'action_rename', 'action_mkdir',
           'action_copytree', 'action_copylist', 'action_copyfile',
           'action_symlink', 'action_chown',
           'action_chown_setuid', 'action_chmod_x', 'action_make_private',
           'filter_mutate', 'get_svn_revision', 'InstallList',
           'make_install_path', 'wwwuid']

# Determine which Python version (2.4 or 2.5, for example) we are running,
# and use that as the filename to the Python directory.
# Just get the first 3 characters of sys.version.
PYTHON_VERSION = sys.version[0:3]

# Location of standard programs
RSYNC = '/usr/bin/rsync'

# UID of the Webserver
wwwuid = 33

def copy_file_to_jail(src, dry):
    """Copies a single file from an absolute location into the same location
    within the jail. src must begin with a '/'. The jail will be located
    in a 'jail' subdirectory of the current path."""
    action_copyfile(src, 'jail' + src, dry)

# The actions call Python os functions but print actions and handle dryness.
# May still throw os exceptions if errors occur.

class RunError:
    """Represents an error when running a program (nonzero return)."""
    def __init__(self, prog, retcode):
        self.prog = prog
        self.retcode = retcode
    def __str__(self):
        return str(self.prog) + " returned " + repr(self.retcode)

def action_runprog(prog, args, dry):
    """Runs a unix program. Searches in $PATH. Synchronous (waits for the
    program to return). Runs in the current environment. First prints the
    action as a "bash" line.

    Throws a RunError with a retcode of the return value of the program,
    if the program did not return 0.

    prog: String. Name of the program. (No path required, if in $PATH).
    args: [String]. Arguments to the program. (Note, this does not allow you to
        set argv[0]; it will always be prog.)
    dry: Bool. If True, prints but does not execute.
    """
    print prog, string.join(args, ' ')
    if dry: return
    ret = os.spawnvp(os.P_WAIT, prog, [prog] + args)
    if ret != 0:
        raise RunError(prog, ret)

def action_remove(path, dry):
    """Calls rmtree, deleting the target file if it exists."""
    try:
        print "rm -r", path
        if not dry:
            shutil.rmtree(path, True)
    except OSError, (err, msg):
        if err != errno.EEXIST:
            raise
        # Otherwise, didn't exist, so we don't care

def action_rename(src, dst, dry):
    """Calls rename. Deletes the target if it already exists."""
    action_remove(dst, dry)
    print "mv ", src, dst
    if dry: return
    try:
        os.rename(src, dst)
    except OSError, (err, msg):
        if err != errno.EEXIST:
            raise

def action_mkdir(path, dry):
    """Calls mkdir. Silently ignored if the directory already exists.
    Creates all parent directories as necessary."""
    print "mkdir -p", path
    if dry: return
    try:
        os.makedirs(path)
    except OSError, (err, msg):
        if err != errno.EEXIST:
            raise

def action_copytree(src, dst, dry):
    """Copies an entire directory tree. Symlinks are seen as normal files and
    copies of the entire file (not the link) are made. Creates all parent
    directories as necessary.

    See shutil.copytree."""
    # Allow copying over itself
    if (os.path.normpath(os.path.join(os.getcwd(),src)) ==
        os.path.normpath(os.path.join(os.getcwd(),dst))):
        return
    
    # Try to do the copy with rsync, if that fails just copy
    try:
        action_runprog(RSYNC, ['-a','--delete',src + '/',dst], dry)
    except RunError:
        if dry: return
        action_remove(dst, dry)
        print "cp -r", src, dst
        shutil.copytree(src, dst, True)

def action_copylist(srclist, dst, dry, srcdir=".", onlybasename=False):
    """Copies all files in a list to a new location. The files in the list
    are read relative to the current directory, and their destinations are the
    same paths relative to dst. Creates all parent directories as necessary.
    srcdir is "." by default, can be overridden.

    If onlybasename is True, only the basename of the source is appended to
    the destination.
    """
    for srcfile in srclist:
        if onlybasename:
            dstfile = os.path.join(dst, os.path.basename(srcfile))
        else:
            dstfile = os.path.join(dst, srcfile)
        srcfile = os.path.join(srcdir, srcfile)
        dstdir = os.path.split(dstfile)[0]
        if not os.path.isdir(dstdir):
            action_mkdir(dstdir, dry)
        print "cp -f", srcfile, dstfile
        if not dry:
            try:
                shutil.copyfile(srcfile, dstfile)
                shutil.copymode(srcfile, dstfile)
            except shutil.Error:
                pass

def action_copyfile(src, dst, dry):
    """Copies one file to a new location. Creates all parent directories
    as necessary.
    Warn if file not found.
    """
    dstdir = os.path.split(dst)[0]
    if not os.path.isdir(dstdir):
        action_mkdir(dstdir, dry)
    print "cp -f", src, dst
    if not dry:
        try:
            shutil.copyfile(src, dst)
            shutil.copymode(src, dst)
        except (shutil.Error, IOError), e:
            print "Warning: " + str(e)

def action_symlink(src, dst, dry):
    """Creates a symlink in a given location. Creates all parent directories
    as necessary.
    """
    dstdir = os.path.split(dst)[0]
    if not os.path.isdir(dstdir):
        action_mkdir(dstdir, dry)
    # Delete existing file
    if os.path.exists(dst):
        os.remove(dst)
    print "ln -fs", src, dst
    if not dry:
        os.symlink(src, dst)

def action_chown_setuid(file, dry):
    """Chowns a file to root, and sets the setuid bit on the file.
    Calling this function requires the euid to be root.
    The actual mode of path is set to: rws--s--s
    """
    print "chown root:root", file
    if not dry:
        os.chown(file, 0, 0)
    print "chmod a+xs", file
    print "chmod u+rw", file
    if not dry:
        os.chmod(file, stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            | stat.S_ISUID | stat.S_IRUSR | stat.S_IWUSR)

def action_chmod_x(file, dry):
    """Chmod 755 a file (sets permissions to rwxr-xr-x)."""
    print "chmod 755", file
    if not dry:
        os.chmod(file, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR
            | stat.S_IXGRP | stat.S_IRGRP | stat.S_IXOTH | stat.S_IROTH)

def action_chown(file, uid, gid, dry):
    """Chowns a file to the specified numeric UID and GID."""
    print "chown %s:%s %s"%(uid, gid, file)
    if not dry:
        os.chown(file, uid, gid)

def action_make_private(file, dry):
    """Ensures that a file is private to IVLE (chowns to www-data and chmod to 
    600)"""
    action_chown(file, wwwuid, wwwuid, dry)
    print "chmod 600", file
    if not dry:
        os.chmod(file, stat.S_IRUSR | stat.S_IWUSR)

def filter_mutate(function, list):
    """Like built-in filter, but mutates the given list instead of returning a
    new one. Returns None."""
    i = len(list)-1
    while i >= 0:
        # Delete elements which do not match
        if not function(list[i]):
            del list[i]
        i -= 1

def get_svn_revision():
    """Returns either the current SVN revision of this build, or None"""
    import pysvn
    try:
        svn = pysvn.Client()
        entry = svn.info('.')
        revnum = entry.revision.number
    except pysvn.ClientError, e:
        revnum = None
    return revnum

### InstallList and helpers ###

# Mime types which will automatically be placed in the list by InstallList.
installlist_mimetypes = ['text/x-python', 'text/html',
    'application/x-javascript', 'application/javascript',
    'text/css', 'image/png', 'image/gif', 'application/xml']
# Filenames which will automatically be placed in the list by InstallList.
whitelist_filenames = ['ivle-spec.conf']

def build_list_py_files(dir, no_top_level=False):
    """Builds a list of all py files found in a directory and its
    subdirectories. Returns this as a list of strings.
    no_top_level=True means the file paths will not include the top-level
    directory.
    """
    pylist = []
    for (dirpath, dirnames, filenames) in os.walk(dir):
        # Exclude directories beginning with a '.' (such as '.svn')
        filter_mutate(lambda x: x[0] != '.', dirnames)
        # All *.py files are added to the list
        pylist += [os.path.join(dirpath, item) for item in filenames
            if mimetypes.guess_type(item)[0] in installlist_mimetypes or
               item in whitelist_filenames]
    if no_top_level:
        for i in range(0, len(pylist)):
            _, pylist[i] = pylist[i].split(os.sep, 1)
    return pylist

def make_install_path(rootdir, path):
    '''Combine an installation root directory and final install path.

    Normalises path, and joins it to the end of rootdir, removing the leading
    / to make it relative if required.
    '''
    normpath = os.path.normpath(path)
    if normpath.startswith(os.sep):
        normpath = normpath[1:]
    return os.path.join(rootdir, normpath)

class InstallList(object):
    list_ivle_lib = property(lambda self: build_list_py_files('ivle'))

    list_subjects = property(lambda self: build_list_py_files('subjects',
                             no_top_level=True))

    list_exercises = property(lambda self: build_list_py_files('exercises',
                              no_top_level=True))

    list_services = [
        "services/python-console",
        "services/fileservice",
        "services/serveservice",
        "services/usrmgt-server",
        "services/diffservice",
        "services/svnlogservice",
        "services/usrmgt-server", # XXX: Should be in bin/
    ]

    list_user_binaries = [
        "bin/ivle-enrol",
        "bin/ivle-enrolallusers",
        "bin/ivle-listusers",
        "bin/ivle-makeuser",
        "bin/ivle-marks",
        "bin/ivle-mountallusers",
        "bin/ivle-remakeuser",
        "bin/ivle-showenrolment",
        "bin/ivle-config",
        "bin/ivle-createdatadirs",
        "bin/ivle-buildjail",
        "bin/ivle-addexercise",
        "bin/ivle-cloneworksheets",
    ]
