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

import functools
import mimetypes
import os
import subprocess

def handle(req):
    """Handler for the Server application which serves pages."""

    mimetypes.init()
    (type, encoding) = mimetypes.guess_type(req.path)

    if type is None:
        type = 'text/plain'

    req.write_html_head_foot = False

    # Get the username of the student whose work we are browsing, and the path
    # on the local machine where the file is stored.
    (user, path) = studpath.url_to_local(req.path)

    if user is None:
        # TODO: Nicer 404 message?
        req.throw_error(req.HTTP_NOT_FOUND)

    # If this type has a special interpreter, call that instead of just
    # serving the content.
    if type in executable_types:
        return executable_types[type](path, req)
    else:
        req.content_type = type
        req.sendfile(path)

# Used to store mutable data
class Dummy:
    pass

def execute_cgi(filename, studentprog, req):
    """
    filename: Full path on the local system to the CGI wrapper program
        being executed.
    studentprog: Full path on the local system to the CGI student program
        which will eventually be executed.
    req: IVLE request object.

    The called CGI wrapper application shall be called using popen and receive
    the HTTP body on stdin. It shall receive the CGI environment variables to
    its environment.
    """

    # Get the student program's directory and execute it from that context.
    slashloc = studentprog.rfind(os.sep)
    if slashloc >= 0:
        progdir = studentprog[0:slashloc]
    else:
        progdir = "/"

    # TODO: Don't create a file if the body length is known to be 0
    # Write the HTTP body to a temporary file so it can be passed as a *real*
    # file to popen.
    f = os.tmpfile()
    body = req.read()
    if body is not None:
        f.write(body)
        f.flush()
        f.seek(0)       # Rewind, for reading

    pid = subprocess.Popen([filename, studentprog],
        stdin=f, stdout=subprocess.PIPE, cwd=progdir)

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

# Mapping of mime types to executables

executable_types = {
    'text/x-python'
        : functools.partial(execute_cgi, '/usr/bin/python'),
}

