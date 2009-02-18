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

from ivle import studpath
from ivle.util import IVLEError, IVLEJailError
import ivle.conf

import functools

import os
import pwd
import subprocess
import cgi

# TODO: Make progressive output work
# Question: Will having a large buffer size stop progressive output from
# working on smaller output

CGI_BLOCK_SIZE = 65535

def interpret_file(req, owner, jail_dir, filename, interpreter, gentle=True):
    """Serves a file by interpreting it using one of IVLE's builtin
    interpreters. All interpreters are intended to run in the user's jail. The
    jail location is provided as an argument to the interpreter but it is up
    to the individual interpreters to create the jail.

    req: An IVLE request object.
    owner: The user who owns the file being served.
    jail_dir: Absolute path to the user's jail.
    filename: Absolute filename within the user's jail.
    interpreter: A function object to call.
    """
    # We can't test here whether or not the target file actually exists,
    # because the apache user may not have permission. Instead we have to
    # rely on the interpreter generating an error.
    if filename.startswith(os.sep):
        filename_abs = filename
        filename_rel = filename[1:]
    else:
        filename_abs = os.path.join(os.sep, filename)
        filename_rel = filename

    # (Note: files are executed by their owners, not the logged in user.
    # This ensures users are responsible for their own programs and also
    # allows them to be executed by the public).

    # Split up req.path again, this time with respect to the jail
    (working_dir, _) = os.path.split(filename_abs)
    # jail_dir is the absolute jail directory.
    # path is the filename relative to the user's jail.
    # working_dir is the directory containing the file relative to the user's
    # jail.
    # (Note that paths "relative" to the jail actually begin with a '/' as
    # they are absolute in the jailspace)

    return interpreter(owner.unixid, jail_dir, working_dir, filename_abs, req,
                       gentle)

class CGIFlags:
    """Stores flags regarding the state of reading CGI output.
       If this is to be gentle, detection of invalid headers will result in an
       HTML warning."""
    def __init__(self, begentle=True):
        self.gentle = begentle
        self.started_cgi_body = False
        self.got_cgi_headers = False
        self.wrote_html_warning = False
        self.linebuf = ""
        self.headers = {}       # Header names : values

def execute_cgi(interpreter, trampoline, uid, jail_dir, working_dir,
                script_path, req, gentle):
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

    # Support no-op trampoline runs.
    if interpreter is None:
        interpreter = '/bin/true'
        script_path = ''
        noop = True
    else:
        noop = False

    # Get the student program's directory and execute it from that context.
    (tramp_dir, _) = os.path.split(trampoline)

    # TODO: Don't create a file if the body length is known to be 0
    # Write the HTTP body to a temporary file so it can be passed as a *real*
    # file to popen.
    f = os.tmpfile()
    body = req.read() if not noop else None
    if body is not None:
        f.write(body)
        f.flush()
        f.seek(0)       # Rewind, for reading

    # Set up the environment
    # This automatically asks mod_python to load up the CGI variables into the
    # environment (which is a good first approximation)
    old_env = os.environ.copy()
    for k in os.environ.keys():
        del os.environ[k]
    for (k,v) in req.get_cgi_environ().items():
        os.environ[k] = v
    fixup_environ(req, script_path)

    # usage: tramp uid jail_dir working_dir script_path
    pid = subprocess.Popen(
        [trampoline, str(uid), ivle.conf.jail_base, ivle.conf.jail_src_base,
         ivle.conf.jail_system, jail_dir, working_dir, interpreter,
        script_path],
        stdin=f, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=tramp_dir)

    # Restore the environment
    for k in os.environ.keys():
        del os.environ[k]
    for (k,v) in old_env.items():
        os.environ[k] = v

    # We don't want any output! Bail out after the process terminates.
    if noop:
        pid.communicate()
        return

    # process_cgi_line: Reads a single line of CGI output and processes it.
    # Prints to req, and also does fancy HTML warnings if Content-Type
    # omitted.
    cgiflags = CGIFlags(gentle)

    # Read from the process's stdout into req
    data = pid.stdout.read(CGI_BLOCK_SIZE)
    while len(data) > 0:
        process_cgi_output(req, data, cgiflags)
        data = pid.stdout.read(CGI_BLOCK_SIZE)

    # If we haven't processed headers yet, now is a good time
    if not cgiflags.started_cgi_body:
        process_cgi_output(req, '\n', cgiflags)

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
        if cgiflags.wrote_html_warning:
            # HTML escape text if wrote_html_warning
            req.write(cgi.escape(data))
        else:
            req.write(data)
    else:
        # Break data into lines of CGI header data. 
        linebuf = cgiflags.linebuf + data
        # First see if we can split all header data
        # We need to get the double CRLF- or LF-terminated headers, whichever
        # is smaller, as either sequence may appear somewhere in the body.
        usplit = linebuf.split('\n\n', 1)
        wsplit = linebuf.split('\r\n\r\n', 1)
        split = len(usplit[0]) > len(wsplit[0]) and wsplit or usplit
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
            if cgiflags.wrote_html_warning:
                # We're done with headers. Treat the rest as data.
                data = headers + '\n' + data
                break
            split = headers.split('\r\n', 1)
            if len(split) == 1:
                split = headers.split('\n', 1)

        # Is this an internal IVLE error condition?
        hs = cgiflags.headers
        if 'X-IVLE-Error-Type' in hs:
            t = hs['X-IVLE-Error-Type']
            if t == IVLEError.__name__:
                raise IVLEError(int(hs['X-IVLE-Error-Code']),
                                hs['X-IVLE-Error-Message'])
            else:
                try:
                    raise IVLEJailError(hs['X-IVLE-Error-Type'],
                                        hs['X-IVLE-Error-Message'],
                                        hs['X-IVLE-Error-Info'])
                except KeyError:
                    raise IVLEError(500, 'bad error headers written by CGI')

        # Check to make sure the required headers were written
        if cgiflags.wrote_html_warning or not cgiflags.gentle:
            # We already reported an error, that's enough
            pass
        elif "Content-Type" in cgiflags.headers:
            pass
        elif "Location" in cgiflags.headers:
            if ("Status" in cgiflags.headers and req.status >= 300
                and req.status < 400):
                pass
            else:
                message = """You did not write a valid status code for
the given location. To make a redirect, you may wish to try:</p>
<pre style="margin-left: 1em">Status: 302 Found
Location: &lt;redirect address&gt;</pre>"""
                write_html_warning(req, message)
                cgiflags.wrote_html_warning = True
        else:
            message = """You did not print a Content-Type header.
CGI requires that you print a "Content-Type". You may wish to try:</p>
<pre style="margin-left: 1em">Content-Type: text/html</pre>"""
            write_html_warning(req, message)
            cgiflags.wrote_html_warning = True

        # Call myself to flush out the extra bit of data we read
        process_cgi_output(req, data, cgiflags)

def process_cgi_header_line(req, line, cgiflags):
    """Process a line of CGI header data. line is a string representing a
    complete line of text, stripped and without the newline.
    """
    try:
        name, value = line.split(':', 1)
    except ValueError:
        # No colon. The user did not write valid headers.
        # If we are being gentle, we want to help the user understand what
        # went wrong. Otherwise, just admit we screwed up.
        warning = "Warning"
        if not cgiflags.gentle:
            message = """An unexpected server error has occured."""
            warning = "Error"
        elif len(cgiflags.headers) == 0:
            # First line was not a header line. We can assume this is not
            # a CGI app.
            message = """You did not print a CGI header.
CGI requires that you print a "Content-Type". You may wish to try:</p>
<pre style="margin-left: 1em">Content-Type: text/html</pre>"""
        else:
            # They printed some header at least, but there was an invalid
            # header.
            message = """You printed an invalid CGI header. You need to leave
a blank line after the headers, before writing the page contents."""
        write_html_warning(req, message, warning=warning)
        cgiflags.wrote_html_warning = True
        # Handle the rest of this line as normal data
        process_cgi_output(req, line + '\n', cgiflags)
        return

    # Read CGI headers
    value = value.strip()
    if name == "Content-Type":
        req.content_type = value
    elif name == "Location":
        req.location = value
    elif name == "Status":
        # Must be an integer, followed by a space, and then the status line
        # which we ignore (seems like Apache has no way to send a custom
        # status line).
        try:
            req.status = int(value.split(' ', 1)[0])
        except ValueError:
            if not cgiflags.gentle:
                # This isn't user code, so it should be good.
                # Get us out of here!
                raise
            message = """The "Status" CGI header was invalid. You need to
print a number followed by a message, such as "302 Found"."""
            write_html_warning(req, message)
            cgiflags.wrote_html_warning = True
            # Handle the rest of this line as normal data
            process_cgi_output(req, line + '\n', cgiflags)
    else:
        # Generic HTTP header
        # FIXME: Security risk letting users write arbitrary headers?
        req.headers_out.add(name, value)
    cgiflags.headers[name] = value # FIXME: Only the last header will end up here.

def write_html_warning(req, text, warning="Warning"):
    """Prints an HTML warning about invalid CGI interaction on the part of the
    user. text may contain HTML markup."""
    req.content_type = "text/html"
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
    <p><strong>%s</strong>: %s
  </div>
  <div style="margin: 8px;">
    <pre>
""" % (warning, text))

location_cgi_python = os.path.join(ivle.conf.lib_path, "trampoline")

# Mapping of interpreter names (as given in conf/app/server.py) to
# interpreter functions.

interpreter_objects = {
    'cgi-python'
        : functools.partial(execute_cgi, "/usr/bin/python",
            location_cgi_python),
    'noop'
        : functools.partial(execute_cgi, None,
            location_cgi_python),
    # Should also have:
    # cgi-generic
    # python-server-page
}

def fixup_environ(req, script_path):
    """Assuming os.environ has been written with the CGI variables from
    apache, make a few changes for security and correctness.

    Does not modify req, only reads it.
    """
    env = os.environ
    # Comments here are on the heavy side, explained carefully for security
    # reasons. Please read carefully before making changes.

    # Remove DOCUMENT_ROOT and SCRIPT_FILENAME. Not part of CGI spec and
    # exposes unnecessary details about server.
    try:
        del env['DOCUMENT_ROOT']
    except: pass
    try:
        del env['SCRIPT_FILENAME']
    except: pass

    # Remove PATH. The PATH here is the path on the server machine; not useful
    # inside the jail. It may be a good idea to add another path, reflecting
    # the inside of the jail, but not done at this stage.
    try:
        del env['PATH']
    except: pass

    # CGI specifies that REMOTE_HOST SHOULD be set, and MAY just be set to
    # REMOTE_ADDR. Since Apache does not appear to set this, set it to
    # REMOTE_ADDR.
    if 'REMOTE_HOST' not in env and 'REMOTE_ADDR' in env:
        env['REMOTE_HOST'] = env['REMOTE_ADDR']

    env['PATH_INFO'] = ''
    del env['PATH_TRANSLATED']

    normuri = os.path.normpath(req.uri)
    env['SCRIPT_NAME'] = normuri

    # SCRIPT_NAME is the path to the script WITHOUT PATH_INFO.
    # We don't care about these if the script is null (ie. noop).
    # XXX: We check for /home because we don't want to interfere with
    # CGIRequest, which fileservice still uses.
    if script_path and script_path.startswith('/home'):
        normscript = os.path.normpath(script_path)

        uri_into_jail = studpath.url_to_jailpaths(os.path.normpath(req.path))[2]

        # PATH_INFO is wrong because the script doesn't physically exist.
        env['PATH_INFO'] = uri_into_jail[len(normscript):]
        if len(env['PATH_INFO']) > 0:
            env['SCRIPT_NAME'] = normuri[:-len(env['PATH_INFO'])]

    # SERVER_SOFTWARE is actually not Apache but IVLE, since we are
    # custom-making the CGI request.
    env['SERVER_SOFTWARE'] = "IVLE/" + str(ivle.conf.ivle_version)

    # Additional environment variables
    username = studpath.url_to_jailpaths(req.path)[0]
    env['HOME'] = os.path.join('/home', username)

class ExecutionError(Exception):
    pass

def execute_raw(user, jail_dir, working_dir, binary, args):
    '''Execute a binary in a user's jail, returning the raw output.

    The binary is executed in the given working directory with the given
    args. A tuple of (stdout, stderr) is returned.
    '''

    tramp = location_cgi_python
    tramp_dir = os.path.split(location_cgi_python)[0]

    # Fire up trampoline. Vroom, vroom.
    proc = subprocess.Popen(
        [tramp, str(user.unixid), ivle.conf.jail_base,
         ivle.conf.jail_src_base, ivle.conf.jail_system, jail_dir,
         working_dir, binary] + args,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, cwd=tramp_dir, close_fds=True)
    exitcode = proc.wait()

    if exitcode != 0:
        raise ExecutionError('subprocess ended with code %d, stderr %s' %
                             (exitcode, proc.stderr.read()))
    return (proc.stdout.read(), proc.stderr.read())
