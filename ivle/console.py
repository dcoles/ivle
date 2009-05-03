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

# Module: Console
# Author: Matt Giuca, Tom Conway, David Coles (refactor)
# Date: 13/8/2008

# Mainly refactored out of consoleservice

import errno
import cPickle
import hashlib
import os
import random
import socket
import StringIO
import uuid

import cjson

import ivle.conf
from ivle import chat

# Outside Jail
trampoline_path = os.path.join(ivle.conf.lib_path, "trampoline")
# Inside Jail
python_path = "/usr/bin/python"
console_dir = os.path.join(ivle.conf.share_path, 'services')
console_path = os.path.join(console_dir, 'python-console')

class ConsoleError(Exception):
    """ The console failed in some way. This is bad. """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ConsoleException(Exception):
    """ The code being exectuted on the console returned an exception. 
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class TruncateStringIO(StringIO.StringIO):
    """ A class that wraps around StringIO and truncates the buffer when the 
    contents are read (except for when using getvalue).
    """
    def __init__(self, buffer=None):
        StringIO.StringIO.__init__(self, buffer)
    
    def read(self, n=-1):
        """ Read at most size bytes from the file (less if the read hits EOF 
        before obtaining size bytes).

        If the size argument is negative or omitted, read all data until EOF is      
        reached. The bytes are returned as a string object. An empty string is 
        returned when EOF is encountered immediately.

        Truncates the buffer.
        """

        self.seek(0)
        res = StringIO.StringIO.read(self, n)
        self.truncate(0)
        return res

    def readline(self, length=None):
        """ Read one entire line from the file.
 
        A trailing newline character is kept in the string (but may be absent 
        when a file ends with an incomplete line). If the size argument is   
        present and non-negative, it is a maximum byte count (including the      
        trailing newline) and an incomplete line may be returned.

        An empty string is returned only when EOF is encountered immediately.
        
        Note: Unlike stdio's fgets(), the returned string contains null   
        characters ('\0') if they occurred in the input.

        Removes the line from the buffer.
        """

        self.seek(0)
        res = StringIO.StringIO.readline(self, length)
        rest = StringIO.StringIO.read(self)
        self.truncate(0)
        self.write(rest)
        return res

    def readlines(self, sizehint=0):
        """ Read until EOF using readline() and return a list containing the        
        lines thus read.
        
        If the optional sizehint argument is present, instead of reading up to 
        EOF, whole lines totalling approximately sizehint bytes (or more to      
        accommodate a final whole line).

        Truncates the buffer.
        """

        self.seek(0)
        res = StringIO.StringIO.readlines(self, length)
        self.truncate(0)
        return res

class Console(object):
    """ Provides a nice python interface to the console
    """
    def __init__(self, uid, jail_path, working_dir):
        """Starts up a console service for user uid, inside chroot jail 
        jail_path with work directory of working_dir
        """
        super(Console, self).__init__()

        self.uid = uid
        self.jail_path = jail_path
        self.working_dir = working_dir

        # Set up the buffers
        self.stdin = TruncateStringIO()
        self.stdout = TruncateStringIO()
        self.stderr = TruncateStringIO()

        # Fire up the console
        self.restart()

    def restart(self):
        # Empty all the buffers
        self.stdin.truncate(0)
        self.stdout.truncate(0)
        self.stderr.truncate(0)

        # TODO: Check if we are already running a console. If we are shut it 
        # down first.

        # TODO: Figure out the host name the console server is running on.
        self.host = socket.gethostname()

        # Create magic
        # TODO
        self.magic = hashlib.md5(uuid.uuid4().bytes).hexdigest()

        # Try to find a free port on the server.
        # Just try some random ports in the range [3000,8000)
        # until we either succeed, or give up. If you think this
        # sounds risky, it isn't:
        # For N ports (e.g. 5000) with k (e.g. 100) in use, the
        # probability of failing to find a free port in t (e.g. 5) tries
        # is (k / N) ** t (e.g. 3.2*10e-9).

        tries = 0
        while tries < 5:
            self.port = int(random.uniform(3000, 8000))

            # Start the console server (port, magic)
            # trampoline usage: tramp uid jail_dir working_dir script_path args
            # console usage:    python-console port magic
            res = os.spawnv(os.P_WAIT, trampoline_path, [
                trampoline_path,
                str(self.uid),
                ivle.conf.jail_base,
                ivle.conf.jail_src_base,
                ivle.conf.jail_system,
                self.jail_path,
                console_dir,
                python_path,
                console_path,
                str(self.port),
                str(self.magic),
                self.working_dir
                ])

            if res == 0:
                # success
                break;

            tries += 1

        # If we can't start the console after 5 attemps (can't find a free port 
        # during random probing, syntax errors, segfaults) throw an exception.
        if tries == 5:
            raise ConsoleError("Unable to start console service!")

    def __chat(self, cmd, args):
        """ A wrapper around chat.chat to comunicate directly with the 
        console.
        """
        try:
            response = chat.chat(self.host, self.port,
                {'cmd': cmd, 'text': args}, self.magic)
        except socket.error, (enumber, estring):
            if enumber == errno.ECONNREFUSED:
                # Timeout
                raise ConsoleError(
                    "Could not establish a connection to the python console")
            else:
                # Some other error - probably serious
                raise socket.error, (enumber, estring)
        except cjson.DecodeError:
            # Couldn't decode the JSON
            raise ConsoleError(
                "Could not understand the python console response")

        return response

    def __handle_chat(self, cmd, args):
        """ A wrapper around self.__chat that handles all the messy responses 
        of chat for higher level interfaces such as inspect
        """
        # Do the request
        response = self.__chat(cmd, args)

        # Process I/O requests
        while 'output' in response or 'input' in response:
            if 'output' in response:
                self.stdout.write(response['output'])
                response = self.chat()
            elif 'input' in response:
                response = self.chat(self.stdin.readline())

        # Process user exceptions
        if 'exc' in response:
            raise ConsoleException(response['exc'])

        return response

    def chat(self, code=''):
        """ Executes a partial block of code """
        return self.__chat('chat', code)

    def block(self, code):
        """ Executes a block of code and returns the output """
        block = self.__handle_chat('block', code)
        if 'output' in block:
            return block['output']
        elif 'okay' in block:
            return
        else:
            raise ConsoleException("Bad response from console: %s"%str(block))

    def globals(self, globs=None):
        """ Returns a dictionary of the console's globals and optionally set 
        them to a new value
        """
        # Pickle the globals
        pickled_globs = None
        if globs is not None:
            pickled_globs = {}
            for g in globs:
                pickled_globs[g] = cPickle.dumps(globs[g])

        globals = self.__handle_chat('globals', pickled_globs)

        # Unpickle the globals
        for g in globals['globals']:
            globals['globals'][g] = cPickle.loads(globals['globals'][g])

        return globals['globals']
        

    def call(self, function, *args, **kwargs):
        """ Calls a function in the python console. Can take in a list of 
        repr() args and dictionary of repr() values kwargs. These will be 
        evaluated on the server side.
        """
        call_args = {
            'function': function,
            'args': args,
            'kwargs': kwargs}
        call = self.__handle_chat('call', call_args)

        # Unpickle any exceptions
        if 'exception' in call:
            call['exception']['except'] = \
                cPickle.loads(call['exception']['except'])

        return call

    def execute(self, code=''):
        """ Runs a block of code in the python console.
        If an exception was thrown then returns an exception object.
        """
        execute = self.__handle_chat('execute', code)
              
        # Unpickle any exceptions
        if 'exception' in execute:
            return cPickle.loads(execute['exception'])
        else:
            return execute


    def set_vars(self, variables):
        """ Takes a dictionary of varibles to add to the console's global 
        space. These are evaluated in the local space so you can't use this to 
        set a varible to a value to be calculated on the console side.
        """
        vars = {}
        for v in variables:
            vars[v] = repr(variables[v])

        set_vars = self.__handle_chat('set_vars', vars)

        if set_vars.get('response') != 'okay':
            raise ConsoleError("Could not set variables")

    def close(self):
        """ Causes the console process to terminate """
        return self.__chat('terminate', None)
    
class ExistingConsole(Console):
    """ Provides a nice python interface to an existing console.
    Note: You can't restart an existing console since there is no way to infer 
    all the starting parameters. Just start a new Console instead.
    """
    def __init__(self, host, port, magic):
        self.host = host
        self.port = port
        self.magic = magic

        # Set up the buffers
        self.stdin = TruncateStringIO()
        self.stdout = TruncateStringIO()
        self.stderr = TruncateStringIO()

    def restart():
        raise NotImplementedError('You can not restart an existing console')
        
