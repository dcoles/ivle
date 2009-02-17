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
    1. Environment var IVLECONF (path to directory)
    2. /etc/ivle/ivle.conf
    Raises a ConfigError on error.
    """
    if 'IVLECONF' in os.environ:
        fname = os.path.join(os.environ['IVLECONF'], 'ivle.conf')
        if os.path.exists(fname):
            return fname
    if os.path.exists('/etc/ivle/ivle.conf'):
        return '/etc/ivle/ivle.conf'
    raise ConfigError("Could not find IVLE config file")

_NO_VALUE = []
class Config(ConfigObj):
    """
    The configuration object. Can be instantiated with no arguments (will
    implicitly find the ivle.conf file and load it).

    Automatically validates the file against the spec (found in
    ./ivle-spec.conf relative to this module).
    """
    def __init__(self, blank=False, *args, **kwargs):
        """Initialises a new Config object. Searches for the config file,
        loads it, and validates it.
        @param blank: If blank=True, will create a blank config instead, and
        not search for the config file.
        @raise ConfigError: If the config file cannot be found.
        """
        specfile = os.path.join(os.path.dirname(__file__), 'ivle-spec.conf')
        if blank:
            super(Config, self).__init__(configspec=specfile, *args, **kwargs)
        else:
            conffile = search_conffile()
            super(Config, self).__init__(infile=conffile, configspec=specfile,
                                         *args, **kwargs)
            # XXX This doesn't raise errors if it doesn't validate
            self.validate(Validator())

    def set_by_path(self, path, value=_NO_VALUE, comment=None):
        """Writes a value to an option, given a '/'-separated path.
        @param path: '/'-separated path to configuration option.
        @param value: Optional - value to write to the option.
        @param comment: Optional - comment string (lines separated by '\n's).
        Note: If only a comment is being inserted, and the value does not
        exist, fails silently.
        """
        path = path.split('/')
        # Iterate over each segment of the path, and find the section in conf
        # file to insert the value into (use all but the last path segment)
        conf_section = self
        for seg in path[:-1]:
            # Create the section if it isn't there
            if seg not in conf_section:
                conf_section[seg] = {}
            conf_section = conf_section[seg]
        # The final path segment names the key to insert into
        keyname = path[-1]
        if value is not _NO_VALUE:
            conf_section[keyname] = value
        if comment is not None:
            try:
                conf_section[keyname]
            except KeyError:
                pass        # Fail silently
            else:
                conf_section.comments[keyname] = comment.split('\n')

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
