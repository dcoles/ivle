# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2009 The University of Melbourne
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

# Author: William Grant

'''Media file support for the framework.'''

import os
import inspect
import mimetypes

import ivle.conf
from ivle.webapp.base.views import BaseView
from ivle.webapp.base.plugins import ViewPlugin
from ivle.webapp.errors import NotFound, Forbidden

def media_url(req, plugin, path):
    '''Generates a URL to a media file.
    
    Plugin can be a string, in which case it is put into the path literally,
    or a plugin object, in which case its name is looked up.'''
    if not isinstance(plugin, basestring):
        plugin = req.reverse_plugins[plugin]
        
    return os.path.join(ivle.conf.root_dir, '+media', plugin, path)

class MediaFileView(BaseView):
    '''A view for media files.

    This serves static files from directories registered by plugins.

    Plugins wishing to export media should declare a 'media' attribute,
    pointing to the directory to serve (relative to the module's directory).
    The contents of that directory will then be available under
    /+media/python.path.to.module.
    '''
    def __init__(self, req, ns, path):
        self.ns = ns
        self.path = path

    def _make_filename(self, req):
        try:
            plugin = req.plugins[self.ns]
        except KeyError:
            raise NotFound()

        try:
            mediadir = plugin.media
        except AttributeError:
            raise NotFound()

        plugindir = os.path.dirname(inspect.getmodule(plugin).__file__)

        return os.path.join(plugindir, mediadir, self.path)

    def render(self, req):
        # If it begins with ".." or separator, it's illegal. Die.
        if self.path.startswith("..") or self.path.startswith('/'):
            raise Forbidden()

        filename = self._make_filename(req)

        # Find an appropriate MIME type.
        (type, _) = mimetypes.guess_type(filename)
        if type is None:
            type = 'application/octet-stream'

        # Get out if it is unreadable or a directory.
        if not os.access(filename, os.F_OK):
            raise NotFound()
        if not os.access(filename, os.R_OK) or os.path.isdir(filename):
            raise Forbidden()

        req.content_type = type
        req.sendfile(filename)

class Plugin(ViewPlugin):
    urls = [
        ('+media/:ns/*path', MediaFileView),
    ]
