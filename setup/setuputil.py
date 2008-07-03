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

# Module: setup/setuputil
# Author: Matt Giuca, Refactored by David Coles
# Date:   02/07/2008

# setup/setuputil.py
# Contains a set of functions useful for the setup program.

import os
import shutil
import errno
import sys
import pysvn
import string
import stat

# Import modules from the website is tricky since they're in the www
# directory.
sys.path.append('../lib')
import common.makeuser

# Determine which Python version (2.4 or 2.5, for example) we are running,
# and use that as the filename to the Python directory.
# Just get the first 3 characters of sys.version.
PYTHON_VERSION = sys.version[0:3]

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
    args: [String]. Arguments to the program.
    dry: Bool. If True, prints but does not execute.
    """
    print prog, string.join(args, ' ')
    if dry: return
    ret = os.spawnvp(os.P_WAIT, prog, args)
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
    action_remove(dst, dry)
    print "cp -r", src, dst
    if dry: return
    shutil.copytree(src, dst, True)

def action_linktree(src, dst, dry):
    """Hard-links an entire directory tree. Same as copytree but the created
    files are hard-links not actual copies. Removes the existing destination.
    """
    action_remove(dst, dry)
    print "<cp with hardlinks> -r", src, dst
    if dry: return
    common.makeuser.linktree(src, dst)

def action_copylist(srclist, dst, dry, srcdir="."):
    """Copies all files in a list to a new location. The files in the list
    are read relative to the current directory, and their destinations are the
    same paths relative to dst. Creates all parent directories as necessary.
    srcdir is "." by default, can be overridden.
    """
    for srcfile in srclist:
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

def action_append(ivle_pth, ivle_www):
    file = open(ivle_pth, 'a+')
    file.write(ivle_www + '\n')
    file.close()

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

def query_user(default, prompt):
    """Prompts the user for a string, which is read from a line of stdin.
    Exits silently if EOF is encountered. Returns the string, with spaces
    removed from the beginning and end.

    Returns default if a 0-length line (after spaces removed) was read.
    """
    sys.stdout.write('%s\n    (default: "%s")\n>' % (prompt, default))
    try:
        val = sys.stdin.readline()
    except KeyboardInterrupt:
        # Ctrl+C
        sys.stdout.write("\n")
        sys.exit(1)
    sys.stdout.write("\n")
    # If EOF, exit
    if val == '': sys.exit(1)
    # If empty line, return default
    val = val.strip()
    if val == '': return default
    return val

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
    try:
        svn = pysvn.Client()
        entry = svn.info('.')
        revnum = entry.revision.number
    except pysvn.ClientError, e:
        revnum = None
    return revnum

