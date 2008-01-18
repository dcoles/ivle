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

# Module: Interpret
# Author: Matt Giuca
# Date: 18/1/2008

# Runs a student script in a safe execution environment.

from common import studpath
import conf
import functools

import os
import pwd
import subprocess

CGI_BLOCK_SIZE = 65535

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
    # jail_dir is the absolute jail directory.
    # path is the filename relative to the user's jail.
    # working_dir is the directory containing the file relative to the user's
    # jail.
    # (Note that paths "relative" to the jail actually begin with a '/' as
    # they are absolute in the jailspace)

    return interpreter(uid, jail_dir, working_dir, path, req)

class CGIFlags:
    """Stores flags regarding the state of reading CGI output."""
    def __init__(self):
        self.got_cgi_header = False
        self.started_cgi_body = False
        self.wrote_html_warning = False
        self.linebuf = ""

def execute_cgi(interpreter, trampoline, uid, jail_dir, working_dir,
                script_path, req):
    """
    trampoline: Full path on the local system to the CGI wrapper program
        being executed.
    uid: User ID of the owner of the file.
    jail_dir: Absolute path of owner's jail directory.
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
        [trampoline, str(uid), jail_dir, working_dir, interpreter,
        script_path],
        stdin=f, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=tramp_dir)

    # process_cgi_line: Reads a single line of CGI output and processes it.
    # Prints to req, and also does fancy HTML warnings if Content-Type
    # omitted.
    cgiflags = CGIFlags()

    # Read from the process's stdout into req
    data = pid.stdout.read(CGI_BLOCK_SIZE)
    while len(data) > 0:
        process_cgi_output(req, data, cgiflags)
        data = pid.stdout.read(CGI_BLOCK_SIZE)

    # If we wrote an HTML warning header, write the footer
    if cgiflags.wrote_html_warning:
        req.write("""</pre>
  </div>
</body>
</html>""")

def process_cgi_output(req, data, cgiflags):
    """Processes a chunk of CGI output. data is a string of arbitrary length;
    some arbitrary chunk of output written by the CGI script."""
    if cgiflags.started_cgi_body:
        # FIXME: HTML escape text if wrote_html_warning
        req.write(data)
    else:
        # Break data into lines of CGI header data. 
        linebuf = cgiflags.linebuf + data
        # First see if we can split all header data
        split = linebuf.split('\r\n\r\n', 1)
        if len(split) == 1:
            # Allow UNIX newlines instead
            split = linebuf.split('\n\n', 1)
        if len(split) == 1:
            # Haven't seen all headers yet. Buffer and come back later.
            cgiflags.linebuf = linebuf
            return

        headers = split[0]
        data = split[1]
        cgiflags.linebuf = ""
        cgiflags.started_cgi_body = True
        # Process all the header lines
        split = headers.split('\r\n', 1)
        if len(split) == 1:
            split = headers.split('\n', 1)
        while True:
            process_cgi_header_line(req, split[0], cgiflags)
            if len(split) == 1: break
            headers = split[1]
            split = headers.split('\r\n', 1)
            if len(split) == 1:
                split = headers.split('\n', 1)

        # Call myself to flush out the extra bit of data we read
        process_cgi_output(req, data, cgiflags)

def process_cgi_header_line(req, line, cgiflags):
    """Process a line of CGI header data. line is a string representing a
    complete line of text, stripped and without the newline.
    Will set cgiflags.started_cgi_body when it detects an empty line, so the
    caller should realise this and change to byte stream output mode.
    """
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
        write_html_warning(req,
"""You did not print a "Content-Type" header.
CGI requires you to print some content type. You may wish to try:</p>
<pre style="margin-left: 1em">Content-Type: text/html</pre>""", cgiflags)
        cgiflags.got_cgi_header = True
        cgiflags.started_cgi_body = True
        req.write(line)

def write_html_warning(req, text, cgiflags):
    """Prints an HTML warning about invalid CGI interaction on the part of the
    user. text may contain HTML markup."""
    req.write("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type"
    content="text/html; charset=utf-8" />
</head>
<body style="margin: 0; padding: 0; font-family: sans-serif;">
  <div style="background-color: #faa; border-bottom: 1px solid black;
    padding: 8px;">
    <p><strong>Warning</strong>: %s
  </div>
  <div style="margin: 8px;">
    <pre>
""" % text)
    cgiflags.wrote_html_warning = True
    

location_cgi_python = os.path.join(conf.ivle_install_dir,
    "bin/trampoline")

# Mapping of interpreter names (as given in conf/app/server.py) to
# interpreter functions.

interpreter_objects = {
    'cgi-python'
        : functools.partial(execute_cgi, "/usr/bin/python",
            location_cgi_python),
    # Should also have:
    # cgi-generic
    # python-server-page
}

