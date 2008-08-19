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
import md5
import os
import random
import socket
import uuid

import cjson

import conf
from common import (chat, util)

# Outside Jail
trampoline_path = os.path.join(conf.ivle_install_dir, "bin/trampoline")
# Inside Jail
python_path = "/usr/bin/python"
console_dir = "/opt/ivle/scripts"
console_path = "/opt/ivle/scripts/python-console"

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

class Console(object):
    """ Provides a nice python interface to the console
    """
    def __init__(self, uid, jail_path, working_dir):
        """Starts up a console service for user uid, inside chroot jail 
        jail_path with work directory of working_dir
        """
        self.uid = uid
        self.jail_path = jail_path
        self.working_dir = working_dir
        self.restart()

    def restart(self):
        # TODO: Check if we are already running a console. If we are shut it 
        # down first.

        # TODO: Figure out the host name the console server is running on.
        self.host = socket.gethostname()

        # Create magic
        # TODO
        self.magic = md5.new(uuid.uuid4().bytes).digest().encode('hex')

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
            cmd = ' '.join([
                trampoline_path,
                str(self.uid),
                self.jail_path,
                console_dir,
                python_path,
                console_path,
                str(self.port),
                str(self.magic),
                self.working_dir
                ])

            res = os.system(cmd)

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

        # Look for user errors
        if 'exc' in response:
            raise ConsoleException(response['exc'])
        
        return response

    def chat(self, code=''):
        """ Executes a partial block of code """
        return self.__chat('chat', code)

    def block(self, code):
        """ Executes a block of code and returns the output """
        block = self.__chat('block', code)
        if 'output' in block:
            return block['output']
        elif 'okay' in block:
            return
        else:
            raise ConsoleException("Bad response from console: %s"%str(block))

    def flush(self, globs=None):
        """ Resets the consoles globals() to the default and optionally augment 
        them with a dictionary simple globals. (Must be able to be pickled)
        """
        # Pickle the globals
        pickled_globs = {}
        if globs is not None:
            for g in globs:
                pickled_globs[g] = cPickle.dumps(globs[g])

        flush = self.__chat('flush', pickled_globs)
        if 'response' in flush and flush['response'] == 'okay':
            return
        else:
            raise ConsoleError("Bad response from console: %s"%str(flush))

    def call(self, function, *args, **kwargs):
        """ Calls a function in the python console. Can take in a list of 
        repr() args and dictionary of repr() values kwargs. These will be 
        evaluated on the server side.
        """
        call_args = {
            'function': function,
            'args': args,
            'kwargs': kwargs}
        call = self.__chat('call', call_args)
        
        # Unpickle any exceptions
        if 'exception' in call:
            call['exception']['except'] = \
                cPickle.loads(call['exception']['except'])

        return call

    def inspect(self, code=''):
        """ Runs a block of code in the python console returning a dictionary 
        summary of the evaluation. Currently this includes the values of 
        stdout, stderr, simple global varibles.
        If an exception was thrown then this dictionary also includes a 
        exception dictionary containg a traceback string and the exception 
        except.
        """
        inspection = self.__chat('inspect', code)
       
        # Unpickle the globals
        for g in inspection['globals']:
            inspection['globals'][g] = cPickle.loads(inspection['globals'][g])
        
        # Unpickle any exceptions
        if 'exception' in inspection:
            inspection['exception']['except'] = \
                cPickle.loads(inspection['exception']['except'])

        return inspection

    def set_vars(self, variables):
        """ Takes a dictionary of varibles to add to the console's global 
        space. These are evaluated in the local space so you can't use this to 
        set a varible to a value to be calculated on the console side.
        """
        vars = {}
        for v in variables:
            vars[v] = repr(variables[v])

        set_vars = self.__chat('set_vars', vars)

        if set_vars.get('response') != 'okay':
            raise ConsoleError("Could not set variables")

    def close(self):
        """ Causes the console process to terminate """
        self.__chat('restart', None)
    

