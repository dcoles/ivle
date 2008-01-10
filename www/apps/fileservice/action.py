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
# action=putfile: Upload a file to the student workspace, and optionally
#               accept zip files which will be unpacked.
#       path:   The path to the file to be written. If it exists, will
#               overwrite. Error if the target file is a directory.
#       data:   Bytes to be written to the file verbatim. May either be
#               a string variable or a file upload.
#       unpack: Optional. If "true", and the data is a valid ZIP file,
#               will create a directory instead and unpack the ZIP file
#               into it.
#
# action=putfiles: Upload multiple files to the student workspace, and
#                 optionally accept zip files which will be unpacked.
#       path:   The path to the DIRECTORY to place files in. Must not be a
#               file.
#       data:   A file upload (may not be a simple string). The filename
#               will be used to determine the target filename within
#               the given path.
#       unpack: Optional. If "true", if any data is a valid ZIP file,
#               will create a directory instead and unpack the ZIP file
#               into it.
#
# The differences between putfile and putfiles are:
# * putfile can only accept a single file.
# * putfile can accept string data, doesn't have to be a file upload.
# * putfile ignores the upload filename, the entire filename is specified on
#       path. putfiles calls files after the name on the user's machine.
#
# Clipboard-based actions. Cut/copy/paste work in the same way as modern
# file browsers, by keeping a server-side clipboard of files that have been
# cut and copied. The clipboard is stored in the session data, so it persists
# across navigation, tabs and browser windows, but not across browser
# sessions.
# 
# action=copy: Write file(s) to the session-based clipboard. Overrides any
#               existing clipboard data. Does not actually copy the file.
#               The files are physically copied when the clipboard is pasted.
#       path:   The path to the file or directory to copy. Can be specified
#               multiple times.
# 
# action=cut: Write file(s) to the session-based clipboard. Overrides any
#               existing clipboard data. Does not actually move the file.
#               The files are physically moved when the clipboard is pasted.
#       path:   The path to the file or directory to cut. Can be specified
#               multiple times.
# 
# action=paste: Copy or move the files stored in the clipboard. Clears the
#               clipboard. The files are copied or moved to a specified dir.
#       path:   The path to the DIRECTORY to paste the files to. Must not
#               be a file.
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
#       path:   The path to the file to be updated. Can be specified multiple
#               times.
#
# action=svncommit: Commit a file(s) or directory(s) to the repository.
#       path:   The path to the file or directory to be committed. Can be
#               specified multiple times. Directories are committed
#               recursively.
#       logmsg: Text of the log message. Optional. There is a default log
#               message if unspecified.
# 
# TODO: Implement the following actions:
#   putfiles, svnrevert, svnupdate, svncommit
# TODO: Implement ZIP unpacking in putfile and putfiles.

import os
import shutil

import pysvn

from common import (util, studpath)

# Make a Subversion client object
svnclient = pysvn.Client()

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
    action(req, fields)

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
    if path is None:
        path = req.path
    elif len(path) > 0 and path[0] == os.sep:
        # Relative to student home
        path = path[1:]
    else:
        # Relative to req.path
        path = os.path.join(req.path, path)

    _, r = studpath.url_to_local(path)
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
        raise ActionError("Another file already exists with that name")

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

### ACTIONS ###

def action_remove(req, fields):
    # TODO: Do an SVN rm if the file is versioned.
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

def action_putfile(req, fields):
    """Writes data to a file, overwriting it if it exists and creating it if
    it doesn't.

    Reads fields: 'path', 'data' (file upload)
    """
    path = fields.getfirst('path')
    data = fields.getfirst('data')
    if path is None or data is None:
        raise ActionError("Required field missing")
    path = actionpath_to_local(req, path)
    data = data.file

    # Copy the contents of file object 'data' to the path 'path'
    try:
        dest = open(path, 'wb')
        shutil.copyfileobj(data, dest)
    except OSError:
        raise ActionError("Could not write to target file")

def action_copy_or_cut(req, fields, mode):
    """Marks specified files on the clipboard, stored in the
    browser session. Sets clipboard for either a cut or copy operation
    as specified.

    Reads fields: 'path'
    """
    # The clipboard object created conforms to the JSON clipboard
    # specification given at the top of listing.py.
    # Note that we do not check for the existence of files here. That is done
    # in the paste operation.
    files = fields.getlist('path')
    files = map(lambda field: field.value, files)
    clipboard = { "mode" : mode, "base" : req.path, "files" : files }
    session = req.get_session()
    session['clipboard'] = clipboard
    session.save()

def action_copy(req, fields):
    """Marks specified files on the clipboard, stored in the
    browser session. Sets clipboard for a "copy" action.

    Reads fields: 'path'
    """
    action_copy_or_cut(req, fields, "copy")

def action_cut(req, fields):
    """Marks specified files on the clipboard, stored in the
    browser session. Sets clipboard for a "cut" action.

    Reads fields: 'path'
    """
    action_copy_or_cut(req, fields, "cut")

def action_paste(req, fields):
    """Performs the copy or move action with the files stored on
    the clipboard in the browser session. Copies/moves the files
    to the specified directory. Clears the clipboard.

    Reads fields: 'path'
    """
    errormsg = None

    todir = fields.getfirst('path')
    if todir is None:
        raise ActionError("Required field missing")
    todir_local = actionpath_to_local(req, todir)
    if not os.path.isdir(todir_local):
        raise ActionError("Target is not a directory")

    session = req.get_session()
    try:
        clipboard = session['clipboard']
        files = clipboard['files']
        base = clipboard['base']
        if clipboard['mode'] == "copy":
            copy = True
        else:
            copy = False
    except KeyError:
        raise ActionError("Clipboard was empty")

    errorfiles = []
    for file in files:
        # The source must not be interpreted as relative to req.path
        # Add a slash (relative to top-level)
        frompath = os.sep + os.path.join(base, file)
        # The destination is found by taking just the basename of the file
        topath = os.path.join(todir, os.path.basename(file))
        try:
            movefile(req, frompath, topath, copy)
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
    # If errors occured, augment the clipboard and raise ActionError
    if len(errorfiles) > 0:
        clipboard['files'] = errorfiles
        session['clipboard'] = clipboard
        session.save()
        raise ActionError(errormsg)

    # Success: Clear the clipboard
    del session['clipboard']
    session.save()

def action_svnadd(req, fields):
    """Performs a "svn add" to each file specified.

    Reads fields: 'path'
    """
    paths = fields.getlist('path')
    paths = map(lambda path: actionpath_to_local(req, path), paths)

    try:
        svnclient.add(paths, recurse=True, force=True)
    except pysvn.ClientError:
        raise ActionError("One or more files could not be added")

# Table of all action functions #
# Each function has the interface f(req, fields).

actions_table = {
    "remove" : action_remove,
    "move" : action_move,
    "putfile" : action_putfile,

    "copy" : action_copy,
    "cut" : action_cut,
    "paste" : action_paste,

    "svnadd" : action_svnadd,
}
