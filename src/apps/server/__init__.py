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

# App: server
# Author: Tom Conway, Matt Giuca
# Date: 13/12/2007

# Serves content to the user (acting as a web server for students files).
# For most file types we just serve the static file, but
# for python files, we evaluate the python script inside
# our safe execution environment.

from common import (util, studpath)
import conf
import conf.app.server

import functools
import mimetypes
import os
import pwd
import subprocess

def handle(req):
    """Handler for the Server application which serves pages."""
    req.write_html_head_foot = False

    # Get the username of the student whose work we are browsing, and the path
    # on the local machine where the file is stored.
    (user, path) = studpath.url_to_local(req.path)

    if user is None:
        # TODO: Nicer 404 message?
        req.throw_error(req.HTTP_NOT_FOUND)

    serve_file(req, user, path)

def serve_file(req, owner, filename):
    """Serves a file, using one of three possibilities: interpreting the file,
    serving it directly, or denying it and returning a 403 Forbidden error.
    No return value. Writes to req (possibly throwing a server error exception
    using req.throw_error).
    
    req: An IVLE request object.
    owner: Username of the user who owns the file being served.
    filename: Filename in the local file system.
    """

    # First get the mime type of this file
    # (Note that importing common.util has already initialised mime types)
    (type, _) = mimetypes.guess_type(filename)
    if type is None:
        type = conf.app.server.default_mimetype

    # If this type is to be interpreted
    if type in conf.app.server.interpreters:
        interp_name = conf.app.server.interpreters[type]
        try:
            # Get the interpreter function object
            interp_object = interpreter_objects[interp_name]
        except KeyError:
            # TODO: Nicer 500 message (this is due to bad configuration in
            # conf/app/server.py)
            req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR)
        interpret_file(req, owner, filename, interp_object)

    else:
        # Otherwise, use the blacklist/whitelist to see if this file should be
        # served or disallowed
        if conf.app.server.blacklist_served_filetypes:
            toserve = type not in conf.app.server.served_filetypes_blacklist
        else:
            toserve = type in conf.app.server.served_filetypes_whitelist

        # toserve or not toserve
        if not toserve:
            # TODO: Nicer 403 message
            req.throw_error(req.HTTP_FORBIDDEN)
        else:
            serve_file_direct(req, filename, type)

def serve_file_direct(req, filename, type):
    """Serves a file by directly writing it out to the response.

    req: An IVLE request object.
    filename: Filename in the local file system.
    type: String. Mime type to serve the file with.
    """
    if not os.access(filename, os.R_OK):
        req.throw_error(req.HTTP_NOT_FOUND)
    req.content_type = type
    req.sendfile(filename)

def interpret_file(req, owner, filename, interpreter):
    """Serves a file by interpreting it using one of IVLE's builtin
    interpreters. All interpreters are intended to run in the user's jail. The
    jail location is provided as an argument to the interpreter but it is up
    to the individual interpreters to create the jail.

    req: An IVLE request object.
    owner: Username of the user who owns the file being served.
    filename: Filename in the local file system.
    interpreter: A function object to call.
    """
    # Make sure the file exists (otherwise some interpreters may not actually
    # complain).
    # Don't test for execute permission, that will only be required for
    # certain interpreters.
    if not os.access(filename, os.R_OK):
        req.throw_error(req.HTTP_NOT_FOUND)

    # Get the UID of the owner of the file
    # (Note: files are executed by their owners, not the logged in user.
    # This ensures users are responsible for their own programs and also
    # allows them to be executed by the public).
    try:
        (_,_,uid,_,_,_,_) = pwd.getpwnam(owner)
    except KeyError:
        # The user does not exist. This should have already failed the
        # previous test.
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR)

    # Split up req.path again, this time with respect to the jail
    (_, jail_dir, path) = studpath.url_to_jailpaths(req.path)
    path = os.path.join('/', path)
    (working_dir, _) = os.path.split(path)
    # Now jail_dir is the jail directory relative to the jails root.
    # Note that the trampoline has jails root hard-coded for security.
    # path is the filename relative to the user's jail.
    # working_dir is the directory containing the file relative to the user's
    # jail.
    # (Note that paths "relative" to the jail actually begin with a '/' as
    # they are absolute in the jailspace)

    return interpreter(uid, jail_dir, working_dir, path, req)

# Used to store mutable data
class Dummy:
    pass

def execute_cgi(trampoline, uid, jail_dir, working_dir, script_path, req):
    """
    trampoline: Full path on the local system to the CGI wrapper program
        being executed.
    uid: User ID of the owner of the file.
    jail_dir: Owner's jail directory relative to the jails root.
    working_dir: Directory containing the script file relative to owner's
        jail.
    script_path: CGI script relative to the owner's jail.
    req: IVLE request object.

    The called CGI wrapper application shall be called using popen and receive
    the HTTP body on stdin. It shall receive the CGI environment variables to
    its environment.
    """

    # Get the student program's directory and execute it from that context.
    (tramp_dir, _) = os.path.split(trampoline)

    # TODO: Don't create a file if the body length is known to be 0
    # Write the HTTP body to a temporary file so it can be passed as a *real*
    # file to popen.
    f = os.tmpfile()
    body = req.read()
    if body is not None:
        f.write(body)
        f.flush()
        f.seek(0)       # Rewind, for reading

    # usage: tramp uid jail_dir working_dir script_path
    pid = subprocess.Popen(
        [trampoline, str(uid), jail_dir, working_dir, script_path],
        stdin=f, stdout=subprocess.PIPE, cwd=tramp_dir)

    # process_cgi_line: Reads a single line of CGI output and processes it.
    # Prints to req, and also does fancy HTML warnings if Content-Type
    # omitted.
    cgiflags = Dummy()
    cgiflags.got_cgi_header = False
    cgiflags.started_cgi_body = False
    cgiflags.wrote_html_warning = False
    def process_cgi_line(line):
        # FIXME? Issue with binary files (processing per-line?)
        if cgiflags.started_cgi_body:
            # FIXME: HTML escape text if wrote_html_warning
            req.write(line)
        else:
            # Read CGI headers
            if line.strip() == "" and cgiflags.got_cgi_header:
                cgiflags.started_cgi_body = True
            elif line.startswith("Content-Type:"):
                req.content_type = line[13:].strip()
                cgiflags.got_cgi_header = True
            elif line.startswith("Location:"):
                # TODO
                cgiflags.got_cgi_header = True
            elif line.startswith("Status:"):
                # TODO
                cgiflags.got_cgi_header = True
            elif cgiflags.got_cgi_header:
                # Invalid header
                # TODO
                req.write("Invalid header")
                pass
            else:
                # Assume the user is not printing headers and give a warning
                # about that.
                # User program did not print header.
                # Make a fancy HTML warning for them.
                req.content_type = "text/html"
                req.write("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type"
    content="text/html; charset=utf-8" />
</head>
<body style="margin: 0; padding: 0; font-family: sans;">
  <div style="background-color: #faa; border-bottom: 1px solid black;
    padding: 8px;">
    <p><strong>Warning</strong>: You did not print a "Content-Type" header.
    CGI requires you to print some content type. You may wish to try:</p>
    <pre style="margin-left: 1em">Content-Type: text/html</pre>
  </div>
  <div style="margin: 8px;">
    <pre>
""")
                cgiflags.got_cgi_header = True
                cgiflags.wrote_html_warning = True
                cgiflags.started_cgi_body = True
                req.write(line)

    # Read from the process's stdout into req
    for line in pid.stdout:
        process_cgi_line(line)

    # If we wrote an HTML warning header, write the footer
    if cgiflags.wrote_html_warning:
        req.write("""</pre>
  </div>
</body>
</html>""")

# TODO: Replace mytest with cgi trampoline handler script
location_cgi_python = os.path.join(conf.ivlepath, "bin/trampoline-python")

# Mapping of interpreter names (as given in conf/app/server.py) to
# interpreter functions.

interpreter_objects = {
    'cgi-python'
        : functools.partial(execute_cgi, location_cgi_python),
    # Should also have:
    # cgi-generic
    # python-server-page
}

