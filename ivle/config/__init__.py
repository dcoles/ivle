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
import glob
import inspect

from configobj import ConfigObj
from validate import Validator

__all__ = ["ConfigError", "Config"]

class ConfigError(Exception):
    """
    An error reading or writing the configuration file.
    """
    pass

def search_confdir():
    """
    Search for the config file, and return the directory it is in.
    1. Environment var IVLECONF (path to directory)
    2. /etc/ivle
    Raises a ConfigError on error.
    """
    if 'IVLECONF' in os.environ:
        fname = os.path.join(os.environ['IVLECONF'])
        if os.path.exists(fname):
            return fname
    if os.path.exists('/etc/ivle'):
        return '/etc/ivle'
    raise ConfigError("Could not find IVLE config directory")

def get_plugin(pluginstr):
    plugin_path, classname = pluginstr.split('#')
    # Load the plugin module from somewhere in the Python path
    # (Note that plugin_path is a fully-qualified Python module name).
    return (plugin_path,
            getattr(__import__(plugin_path, fromlist=[classname]), classname))

_NO_VALUE = []
class Config(ConfigObj):
    """
    The configuration object. Can be instantiated with no arguments (will
    implicitly find the ivle.conf file and load it).

    Automatically validates the file against the spec (found in
    ./ivle-spec.conf relative to this module).
    """
    def __init__(self, blank=False, plugins=True, *args, **kwargs):
        """Initialises a new Config object. Searches for the config file,
        loads it, and validates it.
        @param blank: If blank=True, will create a blank config instead, and
        not search for the config file.
        @param plugins: If True, will find and index plugins.
        @raise ConfigError: If the config file cannot be found.
        """
        specfile = os.path.join(os.path.dirname(__file__), 'ivle-spec.conf')
        if blank:
            super(Config, self).__init__(configspec=specfile, *args, **kwargs)
        else:
            confdir = search_confdir()
            conffile = os.path.join(confdir, 'ivle.conf')
            super(Config, self).__init__(infile=conffile, configspec=specfile,
                                         interpolation='template',
                                         *args, **kwargs)
            # XXX This doesn't raise errors if it doesn't validate
            self.validate(Validator())

            if not plugins:
                return
            self.plugins = {}
            self.plugin_configs = {}
            # Go through the plugin config files, looking for plugins.
            for pconfn in glob.glob(os.path.join(confdir, 'plugins.d/*.conf')):
                pconf = ConfigObj(pconfn)
                for plugin_section in pconf:
                    # We have a plugin path. Resolve it into a class...
                    plugin_path, plugin = get_plugin(plugin_section)
                    self.plugins[plugin_path] = plugin
                    # ... and add it to the registry.
                    self.plugin_configs[plugin] = pconf[plugin_section]

            # Create a registry mapping plugin classes to paths.
            self.reverse_plugins = dict([(v, k) for (k, v) in
                                         self.plugins.items()])

            # Create an index of plugins by base class.
            self.plugin_index = {}
            for plugin in self.plugins.values():
                # Getmro returns a tuple of all the super-classes of the plugin
                for base in inspect.getmro(plugin):
                    if base not in self.plugin_index:
                        self.plugin_index[base] = []
                    self.plugin_index[base].append(plugin)

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
