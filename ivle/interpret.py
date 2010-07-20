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

import ivle
from ivle import studpath
from ivle.util import IVLEJailError, split_path

import functools

import os
import pwd
import subprocess
import cgi

# TODO: Make progressive output work
# Question: Will having a large buffer size stop progressive output from
# working on smaller output

CGI_BLOCK_SIZE = 65535
PATH = "/usr/local/bin:/usr/bin:/bin"

def interpret_file(req, owner, jail_dir, filename, interpreter, gentle=True,
    overrides=None):
    """Serves a file by interpreting it using one of IVLE's builtin
    interpreters. All interpreters are intended to run in the user's jail. The
    jail location is provided as an argument to the interpreter but it is up
    to the individual interpreters to create the jail.

    req: An IVLE request object.
    owner: The user who owns the file being served.
    jail_dir: Absolute path to the user's jail.
    filename: Absolute filename within the user's jail.
    interpreter: A function object to call.
    gentle: ?
    overrides: A dict mapping env var names to strings, to override arbitrary
        environment variables in the resulting CGI environent.
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

    return interpreter(owner, jail_dir, working_dir, filename_abs, req,
                       gentle, overrides=overrides)

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

def execute_cgi(interpreter, owner, jail_dir, working_dir, script_path,
                req, gentle, overrides=None):
    """
    trampoline: Full path on the local system to the CGI wrapper program
        being executed.
    owner: User object of the owner of the file.
    jail_dir: Absolute path of owner's jail directory.
    working_dir: Directory containing the script file relative to owner's
        jail.
    script_path: CGI script relative to the owner's jail.
    req: IVLE request object.
    gentle: ?
    overrides: A dict mapping env var names to strings, to override arbitrary
        environment variables in the resulting CGI environent.

    The called CGI wrapper application shall be called using popen and receive
    the HTTP body on stdin. It shall receive the CGI environment variables to
    its environment.
    """

    trampoline = os.path.join(req.config['paths']['lib'], 'trampoline')

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
    environ = cgi_environ(req, script_path, owner, overrides=overrides)

    # usage: tramp uid jail_dir working_dir script_path
    cmd_line = [trampoline, str(owner.unixid),
            req.config['paths']['jails']['mounts'],
            req.config['paths']['jails']['src'],
            req.config['paths']['jails']['template'],
            jail_dir, working_dir, interpreter, script_path]
    # Popen doesn't like unicode strings. It hateses them.
    cmd_line = [(s.encode('utf-8') if isinstance(s, unicode) else s)
                for s in cmd_line]
    pid = subprocess.Popen(cmd_line,
        stdin=f, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=tramp_dir, env=environ)

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

        # If not executing in gentle mode (which presents CGI violations
        # to users nicely), check if this an internal IVLE error
        # condition.
        if not cgiflags.gentle:
            hs = cgiflags.headers
            if 'X-IVLE-Error-Type' in hs:
                try:
                    raise IVLEJailError(hs['X-IVLE-Error-Type'],
                                        hs['X-IVLE-Error-Message'],
                                        hs['X-IVLE-Error-Info'])
                except KeyError:
                    raise AssertionError("Bad error headers written by CGI.")

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

    # Check if CGI field-name is valid
    CGI_SEPERATORS = set(['(', ')', '<', '>', '@', ',', ';', ':', '\\', '"',
            '/', '[', ']', '?', '=', '{', '}', ' ', '\t'])
    if any((char in CGI_SEPERATORS for char in name)):
        warning = "Warning"
        if not cgiflags.gentle:
            message = """An unexpected server error has occured."""
            warning = "Error"
        else:
            # Header contained illegal characters
            message = """You printed an invalid CGI header. CGI header
            field-names can not contain any of the following characters: 
            <code>( ) &lt; &gt; @ , ; : \\ " / [ ] ? = { } <em>SPACE 
            TAB</em></code>."""
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

# Mapping of interpreter names (as given in conf/app/server.py) to
# interpreter functions.

interpreter_objects = {
    'cgi-python'
        : functools.partial(execute_cgi, "/usr/bin/python"),
    'noop'
        : functools.partial(execute_cgi, None),
    # Should also have:
    # cgi-generic
    # python-server-page
}

def cgi_environ(req, script_path, user, overrides=None):
    """Gets CGI variables from apache and makes a few changes for security and 
    correctness.

    Does not modify req, only reads it.

    overrides: A dict mapping env var names to strings, to override arbitrary
        environment variables in the resulting CGI environent.
    """
    env = {}
    # Comments here are on the heavy side, explained carefully for security
    # reasons. Please read carefully before making changes.
    
    # This automatically asks mod_python to load up the CGI variables into the
    # environment (which is a good first approximation)
    for (k,v) in req.get_cgi_environ().items():
        env[k] = v

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

        uri_into_jail = studpath.to_home_path(os.path.normpath(req.path))

        # PATH_INFO is wrong because the script doesn't physically exist.
        env['PATH_INFO'] = uri_into_jail[len(normscript):]
        if len(env['PATH_INFO']) > 0:
            env['SCRIPT_NAME'] = normuri[:-len(env['PATH_INFO'])]

    # SERVER_SOFTWARE is actually not Apache but IVLE, since we are
    # custom-making the CGI request.
    env['SERVER_SOFTWARE'] = "IVLE/" + ivle.__version__

    # Additional environment variables
    username = user.login
    env['HOME'] = os.path.join('/home', username)

    if overrides is not None:
        env.update(overrides)
    return env

class ExecutionError(Exception):
    pass

def execute_raw(config, user, jail_dir, working_dir, binary, args):
    '''Execute a binary in a user's jail, returning the raw output.

    The binary is executed in the given working directory with the given
    args. A tuple of (stdout, stderr) is returned.
    '''

    tramp = os.path.join(config['paths']['lib'], 'trampoline')
    tramp_dir = os.path.split(tramp)[0]

    # Fire up trampoline. Vroom, vroom.
    cmd_line = [tramp, str(user.unixid), config['paths']['jails']['mounts'],
         config['paths']['jails']['src'],
         config['paths']['jails']['template'],
         jail_dir, working_dir, binary] + args
    # Popen doesn't like unicode strings. It hateses them.
    cmd_line = [(s.encode('utf-8') if isinstance(s, unicode) else s)
                for s in cmd_line]
    proc = subprocess.Popen(cmd_line,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, cwd=tramp_dir, close_fds=True,
        env={'HOME': os.path.join('/home', user.login),
             'PATH': PATH,
             'USER': user.login,
             'LOGNAME': user.login})

    (stdout, stderr) = proc.communicate()
    exitcode = proc.returncode

    if exitcode != 0:
        raise ExecutionError('subprocess ended with code %d, stderr: "%s"' %
                             (exitcode, stderr))
    return (stdout, stderr)
