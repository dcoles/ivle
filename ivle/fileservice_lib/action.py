# IVLE
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

# Module: File Service / Action
# Author: Matt Giuca
# Date: 10/1/2008

# Handles actions requested by the client as part of the 2-stage process of
# fileservice (the second part being the return listing).

### Actions ###

# The most important argument is "action". This determines which action is
# taken. Note that action, and all other arguments, are ignored unless the
# request is a POST request. The other arguments depend upon the action.
# Note that paths are often specified as arguments. Paths that begin with a
# slash are taken relative to the user's home directory (the top-level
# directory seen when fileservice has no arguments or path). Paths without a
# slash are taken relative to the specified path.

# action=remove: Delete a file(s) or directory(s) (recursively).
#       path:   The path to the file or directory to delete. Can be specified
#               multiple times.
#
# action=move: Move or rename a file or directory.
#       from:   The path to the file or directory to be renamed.
#       to:     The path of the target filename. Error if the file already
#               exists.
#
# action=putfile: Upload a file to the student workspace.
#       path:   The path to the file to be written. Error if the target
#               file is a directory.
#       data:   Bytes to be written to the file verbatim. May either be
#               a string variable or a file upload.
#       overwrite: Optional. If supplied, the file will be overwritten.
#               Otherwise, error if path already exists.
#
# action=putfiles: Upload multiple files to the student workspace, and
#                 optionally accept zip files which will be unpacked.
#       path:   The path to the DIRECTORY to place files in. Must not be a
#               file.
#       data:   A file upload (may not be a simple string). The filename
#               will be used to determine the target filename within
#               the given path.
#       unpack: Optional. If supplied, if any data is a valid ZIP file,
#               will create a directory instead and unpack the ZIP file
#               into it.
#
# action=mkdir: Create a directory. The parent dir must exist.
#       path:   The path to a file which does not exist, but whose parent
#               does. The dir will be made with this name.
#
# The differences between putfile and putfiles are:
# * putfile can only accept a single file, and can't unpack zipfiles.
# * putfile can accept string data, doesn't have to be a file upload.
# * putfile ignores the upload filename, the entire filename is specified on
#       path. putfiles calls files after the name on the user's machine.
#
# action=paste: Copy or move the files to a specified dir.
#       src:    The path to the DIRECTORY to get the files from (relative).
#       dst:    The path to the DIRECTORY to paste the files to. Must not
#               be a file.
#       mode:   'copy' or 'move'
#       file:   File to be copied or moved, relative to src, to a destination
#               relative to dst. Can be specified multiple times.
#
# Subversion actions.
# action=svnadd: Add an existing file(s) to version control.
#       path:   The path to the file to be added. Can be specified multiple
#               times.
#
# action=svnrevert: Revert a file(s) to its state as of the current revision
#               / undo local edits.
#       path:   The path to the file to be reverted. Can be specified multiple
#               times.
#
# action=svnupdate: Bring a file up to date with the head revision.
#       path:   The path to the file to be updated. Only one file may be
#               specified.
#       revision: The revision number to update to. If not provided this
#               defaults to HEAD.
#
# action=svnpublish: Set the "published" flag on a file to True.
#       path:   The path to the file to be published. Can be specified
#               multiple times.
#
# action=svnunpublish: Set the "published" flag on a file to False.
#       path:   The path to the file to be unpublished. Can be specified
#               multiple times.
#
# action=svncommit: Commit a file(s) or directory(s) to the repository.
#       path:   The path to the file or directory to be committed. Can be
#               specified multiple times. Directories are committed
#               recursively.
#       logmsg: Text of the log message. Optional. There is a default log
#               message if unspecified.
# action=svncheckout: Checkout a file/directory from the repository.
#       path:   The [repository] path to the file or directory to be
#               checked out.
# 
# action=svnrepomkdir: Create a directory in a repository (not WC).
#       path:   The path to the directory to be created (under the IVLE
#               repository base).
#       logmsg: Text of the log message.
# 
# action=svnrepostat: Check if a path exists in a repository (not WC).
#       path:   The path to the directory to be checked (under the IVLE
#               repository base).
#
# action=svncleanup: Recursively clean up the working copy, removing locks,
#   resuming unfinished operations, etc.
#       path:   The path to the directory to be cleaned
#
# TODO: Implement the following actions:
#   svnupdate (done?)
# TODO: Implement ZIP unpacking in putfiles (done?).
# TODO: svnupdate needs a digest to tell the user the files that were updated.
#   This can be implemented by some message passing between action and
#   listing, and having the digest included in the listing. (Problem if
#   the listing is not a directory, but we could make it an error to do an
#   update if the path is not a directory).

import os
import cStringIO
import shutil
import urllib

import pysvn

from ivle import (util, studpath, zip)
from ivle.fileservice_lib.exceptions import WillNotOverwrite
import ivle.conf
import ivle.svn

# Make a Subversion client object (which will log in with this user's
# credentials, upon request)
svnclient = ivle.svn.create_auth_svn_client(username=ivle.conf.login,
                                            password=ivle.conf.svn_pass)
svnclient.exception_style = 0               # Simple (string) exceptions

DEFAULT_LOGMESSAGE = "No log message supplied."

# Mime types
# application/json is the "best" content type but is not good for
# debugging because Firefox just tries to download it
mime_dirlisting = "text/html"
#mime_dirlisting = "application/json"

class ActionError(Exception):
    """Represents an error processing an action. This can be
    raised by any of the action functions, and will be caught
    by the top-level handler, put into the HTTP response field,
    and continue.

    Important Security Consideration: The message passed to this
    exception will be relayed to the client.
    """
    pass

def handle_action(req, action, fields):
    """Perform the "action" part of the response.
    This function should only be called if the response is a POST.
    This performs the action's side-effect on the server. If unsuccessful,
    writes the X-IVLE-Action-Error header to the request object. Otherwise,
    does not touch the request object. Does NOT write any bytes in response.

    May throw an ActionError. The caller should put this string into the
    X-IVLE-Action-Error header, and then continue normally.

    action: String, the action requested. Not sanitised.
    fields: FieldStorage object containing all arguments passed.
    """
    global actions_table        # Table of function objects
    try:
        action = actions_table[action]
    except KeyError:
        # Default, just send an error but then continue
        raise ActionError("Unknown action")
    return action(req, fields)

def actionpath_to_urlpath(req, path):
    """Determines the URL path (relative to the student home) upon which the
    action is intended to act. See actionpath_to_local.
    """
    if path is None:
        return req.path
    elif len(path) > 0 and path[0] == os.sep:
        # Relative to student home
        return path[1:]
    else:
        # Relative to req.path
        return os.path.join(req.path, path)

def actionpath_to_local(req, path):
    """Determines the local path upon which an action is intended to act.
    Note that fileservice actions accept two paths: the request path,
    and the "path" argument given to the action.
    According to the rules, if the "path" argument begins with a '/' it is
    relative to the user's home; if it does not, it is relative to the
    supplied path.

    This resolves the path, given the request and path argument.

    May raise an ActionError("Invalid path"). The caller is expected to
    let this fall through to the top-level handler, where it will be
    put into the HTTP response field. Never returns None.

    Does not mutate req.
    """
    r = studpath.to_home_path(actionpath_to_urlpath(req, path))
    if r is None:
        raise ActionError("Invalid path")
    return r

def movefile(req, frompath, topath, copy=False):
    """Performs a file move, resolving filenames, checking for any errors,
    and throwing ActionErrors if necessary. Can also be used to do a copy
    operation instead.

    frompath and topath are straight paths from the client. Will be checked.
    """
    # TODO: Do an SVN mv if the file is versioned.
    # TODO: Disallow tampering with student's home directory
    if frompath is None or topath is None:
        raise ActionError("Required field missing")
    frompath = actionpath_to_local(req, frompath)
    topath = actionpath_to_local(req, topath)
    if not os.path.exists(frompath):
        raise ActionError("The source file does not exist")
    if os.path.exists(topath):
        if frompath == topath:
            raise ActionError("Source and destination are the same")
        raise ActionError("A file already exists with that name")

    try:
        if copy:
            if os.path.isdir(frompath):
                shutil.copytree(frompath, topath)
            else:
                shutil.copy2(frompath, topath)
        else:
            shutil.move(frompath, topath)
    except OSError:
        raise ActionError("Could not move the file specified")
    except shutil.Error:
        raise ActionError("Could not move the file specified")

def svn_movefile(req, frompath, topath, copy=False):
    """Performs an svn move, resolving filenames, checking for any errors,
    and throwing ActionErrors if necessary. Can also be used to do a copy
    operation instead.

    frompath and topath are straight paths from the client. Will be checked.
    """
    if frompath is None or topath is None:
        raise ActionError("Required field missing")
    frompath = actionpath_to_local(req, frompath)
    topath = actionpath_to_local(req, topath)
    if not os.path.exists(frompath):
        raise ActionError("The source file does not exist")
    if os.path.exists(topath):
        if frompath == topath:
            raise ActionError("Source and destination are the same")
        raise ActionError("A file already exists with that name")

    try:
        if copy:
            svnclient.copy(frompath, topath)
        else:
            svnclient.move(frompath, topath)
    except OSError:
        raise ActionError("Could not move the file specified")
    except pysvn.ClientError:
        raise ActionError("Could not move the file specified")  


### ACTIONS ###

def action_delete(req, fields):
    # TODO: Disallow removal of student's home directory
    """Removes a list of files or directories.

    Reads fields: 'path' (multiple)
    """
    paths = fields.getlist('path')
    goterror = False
    for path in paths:
        path = actionpath_to_local(req, path)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError:
            goterror = True
        except shutil.Error:
            goterror = True
    if goterror:
        if len(paths) == 1:
            raise ActionError("Could not delete the file specified")
        else:
            raise ActionError(
                "Could not delete one or more of the files specified")

def action_move(req, fields):
    # TODO: Do an SVN mv if the file is versioned.
    # TODO: Disallow tampering with student's home directory
    """Removes a list of files or directories.

    Reads fields: 'from', 'to'
    """
    frompath = fields.getfirst('from')
    topath = fields.getfirst('to')
    movefile(req, frompath, topath)

def action_mkdir(req, fields):
    """Creates a directory with the given path.
    Reads fields: 'path'
    """
    path = fields.getfirst('path')
    if path is None:
        raise ActionError("Required field missing")
    path = actionpath_to_local(req, path)

    if os.path.exists(path):
        raise ActionError("A file already exists with that name")

    # Create the directory
    try:
        os.mkdir(path)
    except OSError:
        raise ActionError("Could not create directory")

def action_putfile(req, fields):
    """Writes data to a file, overwriting it if it exists and creating it if
    it doesn't.

    Reads fields: 'path', 'data' (file upload), 'overwrite'
    """
    # TODO: Read field "unpack".
    # Important: Data is "None" if the file submitted is empty.
    path = fields.getfirst('path')
    data = fields.getfirst('data')
    if path is None:
        raise ActionError("Required field missing")
    if data is None:
        # Workaround - field reader treats "" as None, so this is the only
        # way to allow blank file uploads
        data = ""
    path = actionpath_to_local(req, path)

    if data is not None:
        data = cStringIO.StringIO(data)

    overwrite = fields.getfirst('overwrite')
    if overwrite is None:
        overwrite = False
    else:
        overwrite = True

    if overwrite:
        # Overwrite files; but can't if it's a directory
        if os.path.isdir(path):
            raise ActionError("A directory already exists "
                    + "with that name")
    else:
        if os.path.exists(path):
            raise ActionError("A file already exists with that name")

    # Copy the contents of file object 'data' to the path 'path'
    try:
        dest = open(path, 'wb')
        if data is not None:
            shutil.copyfileobj(data, dest)
    except (IOError, OSError), e:
        raise ActionError("Could not write to target file: %s" % e.strerror)

def action_putfiles(req, fields):
    """Writes data to one or more files in a directory, overwriting them if
    it they exist.

    Reads fields: 'path', 'data' (file upload, multiple), 'unpack'
    """
    # Important: Data is "None" if the file submitted is empty.
    path = fields.getfirst('path')
    data = fields['data']
    if type(data) != type([]):
        data = [data]
    unpack = fields.getfirst('unpack')
    if unpack is None:
        unpack = False
    else:
        unpack = True
    if path is None:
        raise ActionError("Required field missing")
    path = actionpath_to_urlpath(req, path)
    goterror = False

    for datum in data:
        # Each of the uploaded files
        filepath = os.path.join(path, datum.filename)
        filepath_local = studpath.to_home_path(filepath)
        if os.path.isdir(filepath_local):
            raise ActionError("A directory already exists "
                    + "with that name")
        else:
            if os.path.exists(filepath_local):
                raise ActionError("A file already exists with that name")
        filedata = datum.file

        if unpack and datum.filename.lower().endswith(".zip"):
            # A zip file - unpack it instead of just copying
            # TODO: Use the magic number instead of file extension
            # Note: Just unzip into the current directory (ignore the
            # filename)
            try:
                # First get the entire path (within jail)
                abspath = studpath.to_home_path(path)
                abspath = os.path.join(os.sep, abspath)
                zip.unzip(abspath, filedata)
            except (OSError, IOError):
                goterror = True
            except WillNotOverwrite, e:
                raise ActionError("File '" + e.filename + "' already exists.")
        else:
            # Not a zip file
            filepath_local = studpath.to_home_path(filepath)
            if filepath_local is None:
                raise ActionError("Invalid path")

            # Copy the contents of file object 'data' to the path 'path'
            try:
                dest = open(filepath_local, 'wb')
                if data is not None:
                    shutil.copyfileobj(filedata, dest)
            except (OSError, IOError):
                # TODO: Be more descriptive.
                goterror = True

    if goterror:
        if len(data) == 1:
            raise ActionError("Could not write to target file")
        else:
            raise ActionError(
                "Could not write to one or more of the target files")

def action_paste(req, fields):
    """Performs the copy or move action with the files specified.
    Copies/moves the files to the specified directory.

    Reads fields: 'src', 'dst', 'mode', 'file' (multiple).
    src: Base path that all the files are relative to (source).
    dst: Destination path to paste into.
    mode: 'copy' or 'move'.
    file: (Multiple) Files relative to base, which will be copied
        or moved to new locations relative to path.
    """
    errormsg = None

    dst = fields.getfirst('dst')
    src = fields.getfirst('src')
    mode = fields.getfirst('mode')
    files = fields.getlist('file')
    if dst is None or src is None or mode is None:
        raise ActionError("Required field missing")

    dst_local = actionpath_to_local(req, dst)
    if not os.path.isdir(dst_local):
        raise ActionError("dst is not a directory")

    errorfiles = []
    for file in files:
        # The source must not be interpreted as relative to req.path
        # Add a slash (relative to top-level)
        if src[:1] != '/':
            src = '/' + src
        frompath = os.path.join(src, file)
        # The destination is found by taking just the basename of the file
        topath = os.path.join(dst, os.path.basename(file))
        try:
            if mode == "copy":
                movefile(req, frompath, topath, True)
            elif mode == "move":
                movefile(req, frompath, topath, False)
            elif mode == "svncopy":
                svn_movefile(req, frompath, topath, True)
            elif mode == "svnmove":
                svn_movefile(req, frompath, topath, False)
            else:
                raise ActionError("Invalid mode (must be '(svn)copy' or '(svn)move')")
        except ActionError, message:
            # Store the error for later; we want to copy as many as possible
            if errormsg is None:
                errormsg = message
            else:
                # Multiple errors; generic message
                errormsg = "One or more files could not be pasted"
            # Add this file to errorfiles; it will be put back on the
            # clipboard for possible future pasting.
            errorfiles.append(file)
    if errormsg is not None:
        raise ActionError(errormsg)

    # XXX errorfiles contains a list of files that couldn't be pasted.
    # we currently do nothing with this.

def action_publish(req,fields):
    """Marks the folder as published by adding a '.published' file to the 
    directory and ensuring that the parent directory permissions are correct

    Reads fields: 'path'
    """
    paths = fields.getlist('path')
    user = util.split_path(req.path)[0]
    homedir = "/home/%s" % user
    if len(paths):
        paths = map(lambda path: actionpath_to_local(req, path), paths)
    else:
        paths = [studpath.to_home_path(req.path)]

    # Set all the dirs in home dir world browsable (o+r,o+x)
    #FIXME: Should really only do those in the direct path not all of the 
    # folders in a students home directory
    for root,dirs,files in os.walk(homedir):
        os.chmod(root, os.stat(root).st_mode|0005)

    try:
        for path in paths:
            if os.path.isdir(path):
                pubfile = open(os.path.join(path,'.published'),'w')
                pubfile.write("This directory is published\n")
                pubfile.close()
            else:
                raise ActionError("Can only publish directories")
    except OSError, e:
        raise ActionError("Directory could not be published")

def action_unpublish(req,fields):
    """Marks the folder as unpublished by removing a '.published' file in the 
    directory (if it exits). It does not change the permissions of the parent 
    directories.

    Reads fields: 'path'
    """
    paths = fields.getlist('path')
    if len(paths):
        paths = map(lambda path: actionpath_to_local(req, path), paths)
    else:
        paths = [studpath.to_home_path(req.path)]

    try:
        for path in paths:
            if os.path.isdir(path):
                pubfile = os.path.join(path,'.published')
                if os.path.isfile(pubfile):
                    os.remove(pubfile)
            else:
                raise ActionError("Can only unpublish directories")
    except OSError, e:
        raise ActionError("Directory could not be unpublished")


def action_svnadd(req, fields):
    """Performs a "svn add" to each file specified.

    Reads fields: 'path' (multiple)
    """
    paths = fields.getlist('path')
    paths = map(lambda path: actionpath_to_local(req, path), paths)

    try:
        svnclient.add(paths, recurse=True, force=True)
    except pysvn.ClientError, e:
        raise ActionError(str(e))

def action_svnremove(req, fields):
    """Performs a "svn remove" on each file specified.

    Reads fields: 'path' (multiple)
    """
    paths = fields.getlist('path')
    paths = map(lambda path: actionpath_to_local(req, path), paths)

    try:
        svnclient.remove(paths, force=True)
    except pysvn.ClientError, e:
        raise ActionError(str(e))

def action_svnupdate(req, fields):
    """Performs a "svn update" to each file specified.

    Reads fields: 'path' and 'revision'
    """
    path = fields.getfirst('path')
    revision = fields.getfirst('revision')
    if path is None:
        raise ActionError("Required field missing")
    if revision is None:
        revision = pysvn.Revision( pysvn.opt_revision_kind.head )
    else:
        try:
            revision = pysvn.Revision(pysvn.opt_revision_kind.number,
                    int(revision))
        except ValueError, e:
            raise ActionError("Bad revision number: '%s'"%revision,)
    path = actionpath_to_local(req, path)

    try:
        svnclient.update(path, recurse=True, revision=revision)
    except pysvn.ClientError, e:
        raise ActionError(str(e))

def action_svnresolved(req, fields):
    """Performs a "svn resolved" to each file specified.

    Reads fields: 'path'
    """
    path = fields.getfirst('path')
    if path is None:
        raise ActionError("Required field missing")
    path = actionpath_to_local(req, path)

    try:
        svnclient.resolved(path, recurse=True)
    except pysvn.ClientError, e:
        raise ActionError(str(e))

def action_svnrevert(req, fields):
    """Performs a "svn revert" to each file specified.

    Reads fields: 'path' (multiple)
    """
    paths = fields.getlist('path')
    paths = map(lambda path: actionpath_to_local(req, path), paths)

    try:
        svnclient.revert(paths, recurse=True)
    except pysvn.ClientError, e:
        raise ActionError(str(e))

def action_svnpublish(req, fields):
    """Sets svn property "ivle:published" on each file specified.
    Should only be called on directories (only effective on directories
    anyway).

    Reads fields: 'path'

    XXX Currently unused by the client (calls action_publish instead, which
    has a completely different publishing model).
    """
    paths = fields.getlist('path')
    if len(paths):
        paths = map(lambda path: actionpath_to_local(req, path), paths)
    else:
        paths = [studpath.to_home_path(req.path)]

    try:
        for path in paths:
            # Note: Property value doesn't matter
            svnclient.propset("ivle:published", "", path, recurse=False)
    except pysvn.ClientError, e:
        raise ActionError("Directory could not be published")

def action_svnunpublish(req, fields):
    """Deletes svn property "ivle:published" on each file specified.

    Reads fields: 'path'

    XXX Currently unused by the client (calls action_unpublish instead, which
    has a completely different publishing model).
    """
    paths = fields.getlist('path')
    paths = map(lambda path: actionpath_to_local(req, path), paths)

    try:
        for path in paths:
            svnclient.propdel("ivle:published", path, recurse=False)
    except pysvn.ClientError, e:
        raise ActionError("Directory could not be unpublished")

def action_svncommit(req, fields):
    """Performs a "svn commit" to each file specified.

    Reads fields: 'path' (multiple), 'logmsg' (optional)
    """
    paths = fields.getlist('path')
    paths = map(lambda path: actionpath_to_local(req, str(path)), paths)
    logmsg = str(fields.getfirst('logmsg', DEFAULT_LOGMESSAGE))
    if logmsg == '': logmsg = DEFAULT_LOGMESSAGE

    try:
        svnclient.checkin(paths, logmsg, recurse=True)
    except pysvn.ClientError, e:
        raise ActionError(str(e))

def action_svncheckout(req, fields):
    """Performs a "svn checkout" of the first path into the second path.

    Reads fields: 'path'    (multiple)
    """
    paths = fields.getlist('path')
    if len(paths) != 2:
        raise ActionError("usage: svncheckout url local-path")
    url = ivle.conf.svn_addr + "/" + urllib.quote(paths[0])
    local_path = actionpath_to_local(req, str(paths[1]))
    try:
        svnclient.checkout(url, local_path, recurse=True)
    except pysvn.ClientError, e:
        raise ActionError(str(e))

def action_svnrepomkdir(req, fields):
    """Performs a "svn mkdir" on a path under the IVLE SVN root.

    Reads fields: 'path'
    """
    path = fields.getfirst('path')
    logmsg = fields.getfirst('logmsg')
    url = ivle.conf.svn_addr + "/" + path
    try:
        svnclient.mkdir(url, log_message=logmsg)
    except pysvn.ClientError, e:
        raise ActionError(str(e))

def action_svnrepostat(req, fields):
    """Discovers whether a path exists in a repo under the IVLE SVN root.

    If it does exist, returns a dict containing its metadata.

    Reads fields: 'path'
    """
    path = fields.getfirst('path')
    url = ivle.conf.svn_addr + "/" + path
    svnclient.exception_style = 1

    try:
        info = svnclient.info2(url,
            revision=pysvn.Revision(pysvn.opt_revision_kind.head))[0][1]
        return {'svnrevision': info['rev'].number
                  if info['rev'] and
                     info['rev'].kind == pysvn.opt_revision_kind.number
                  else None}
    except pysvn.ClientError, e:
        # Error code 170000 means ENOENT in this revision.
        if e[1][0][1] == 170000:
            raise util.IVLEError(404, 'The specified repository path does not exist')
        else:
            raise ActionError(str(e[0]))


def action_svncleanup(req, fields):
    """Recursively clean up the working copy, removing locks, resuming 
    unfinished operations, etc.
        path:   The path to be cleaned"""

    path = fields.getfirst('path')
    if path is None:
        raise ActionError("Required field missing")
    path = actionpath_to_local(req, path)

    try:
        svnclient.cleanup(path)
    except pysvn.ClientError, e:
        raise ActionError(str(e))


# Table of all action functions #
# Each function has the interface f(req, fields).

actions_table = {
    "delete" : action_delete,
    "move" : action_move,
    "mkdir" : action_mkdir,
    "putfile" : action_putfile,
    "putfiles" : action_putfiles,
    "paste" : action_paste,
    "publish" : action_publish,
    "unpublish" : action_unpublish,

    "svnadd" : action_svnadd,
    "svnremove" : action_svnremove,
    "svnupdate" : action_svnupdate,
    "svnresolved" : action_svnresolved,
    "svnrevert" : action_svnrevert,
    "svnpublish" : action_svnpublish,
    "svnunpublish" : action_svnunpublish,
    "svncommit" : action_svncommit,
    "svncheckout" : action_svncheckout,
    "svnrepomkdir" : action_svnrepomkdir,
    "svnrepostat" : action_svnrepostat,
    "svncleanup" : action_svncleanup,
}
