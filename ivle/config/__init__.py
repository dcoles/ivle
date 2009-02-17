# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
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

# Author: Matt Giuca, Will Grant

"""
Provides programmatic access to the IVLE configuration file.
"""

import os

from configobj import ConfigObj
from validate import Validator

__all__ = ["ConfigError", "Config"]

class ConfigError(Exception):
    """
    An error reading or writing the configuration file.
    """
    pass

def search_conffile():
    """
    Search for the config file, and return it as a filename.
    1. Environment var IVLECONF (full filename).
    2. ./etc/ivle.conf
    3. /etc/ivle/ivle.conf
    Raises a ConfigError on error.
    """
    if 'IVLECONF' in os.environ:
        fname = os.environ['IVLECONF']
        if os.path.exists(fname):
            return fname
    if os.path.exists('./etc/ivle.conf'):
        return './etc/ivle.conf'
    if os.path.exists('/etc/ivle/ivle.conf'):
        return '/etc/ivle/ivle.conf'
    raise ConfigError("Could not find IVLE config file")

class Config(ConfigObj):
    """
    The configuration object. Can be instantiated with no arguments (will
    implicitly find the ivle.conf file and load it).

    Automatically validates the file against the spec (found in
    ./ivle-spec.conf relative to this module).
    """
    def __init__(self, *args, **kwargs):
        conffile = search_conffile()
        specfile = os.path.join(os.path.dirname(__file__), 'ivle-spec.conf')
        super(Config, self).__init__(infile=conffile, configspec=specfile,
                                     *args, **kwargs)
        # XXX This doesn't raise errors if it doesn't validate
        self.validate(Validator())

    def get_by_path(self, path):
        """Gets an option's value, given a '/'-separated path.
        @param path: '/'-separated path to configuration option.
        @raise KeyError: if no config option is at that path.
        """
        # Iterate over each segment of the path, and find the value in conf file
        value = self
        for seg in path.split('/'):
            value = value[seg]      # May raise KeyError
        return value
