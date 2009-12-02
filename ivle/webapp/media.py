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
import time
import inspect
import mimetypes
import email.utils

from ivle.webapp.base.views import BaseView
from ivle.webapp.base.plugins import PublicViewPlugin, ViewPlugin, MediaPlugin
from ivle.webapp.errors import NotFound, Forbidden
from ivle.webapp.publisher import INF
from ivle.webapp import ApplicationRoot

# This maps a media namespace to an external dependency directory (in this
# case specified by the configuration option media/externals/jquery) and a
# list of permitted subpaths.
EXTERNAL_MEDIA_MAP = {'jquery': ('jquery', ['jquery.js'])}

def media_url(req, plugin, path):
    '''Generates a URL to a media file.

    Plugin can be a string, in which case it is put into the path literally,
    or a plugin object, in which case its name is looked up.

    If a version is specified in the IVLE configuration, a versioned URL will
    be generated.
    '''
    if not isinstance(plugin, basestring):
        plugin = req.config.reverse_plugins[plugin]

    media_path = os.path.join('+media', '+' + req.config['media']['version']) \
                    if req.config['media']['version'] else '+media'

    return req.make_path(os.path.join(media_path, plugin, path))

class MediaFile(object):
    def __init__(self, root, external, version, ns, path):
        self.root = root
        self.external = external
        self.version = version
        self.ns = ns
        self.path = path

    @property
    def filename(self):
        if self.external:
            try:
                extern = EXTERNAL_MEDIA_MAP[self.ns]
            except KeyError:
                return None

            # Unless it's a whitelisted path, we don't want to hear about it.
            if self.path not in extern[1]:
                return None

            # Grab the admin-configured path for this particular external dep.
            externdir = self.root.config['media']['externals'][extern[0]]

            assert isinstance(externdir, basestring)

            return os.path.join(externdir, self.path)
        else:
            try:
                plugin = self.root.config.plugins[self.ns]
            except KeyError:
                return None

            if not issubclass(plugin, MediaPlugin):
                return None

            mediadir = plugin.media
            plugindir = os.path.dirname(inspect.getmodule(plugin).__file__)

            return os.path.join(plugindir, mediadir, self.path)

class MediaFileView(BaseView):
    permission = None

    def render(self, req):
        # If it begins with ".." or separator, it's illegal. Die.
        if self.context.path.startswith("..") or \
           self.context.path.startswith('/'):
            raise Forbidden()

        filename = self.get_filename(req)
        if filename is None:
            raise NotFound()

        # Find an appropriate MIME type.
        (type, _) = mimetypes.guess_type(filename)
        if type is None:
            type = 'application/octet-stream'

        # Get out if it is unreadable or a directory.
        if not os.access(filename, os.F_OK):
            raise NotFound()
        if not os.access(filename, os.R_OK) or os.path.isdir(filename):
            raise Forbidden()

        if self.context.version is not None:
            req.headers_out['Expires'] = email.utils.formatdate(
                                timeval=time.time() + (60*60*24*365),
                                localtime=False,
                                usegmt=True)


        req.content_type = type
        req.sendfile(filename)

    def get_filename(self, req):
        return self.context.filename

    def get_permissions(self, user):
        return set()

def root_to_media(root, *segments):
    if segments[0].startswith('+'):
        if segments[0] == '+external':
            external = True
            version = None
            path = segments[1:]
        else:
            version = segments[0][1:]
            if segments[1] == '+external':
                external = True
                path = segments[2:]
            else:
                external = False
                path = segments[1:]
    else:
        external = False
        version = None
        path = segments

    if version is not None and version != root.config['media']['version']:
        return None

    ns = path[0]
    path = os.path.normpath(os.path.join(*path[1:]))

    return MediaFile(root, external, version, ns, path)

class Plugin(ViewPlugin, PublicViewPlugin):
    forward_routes = [(ApplicationRoot, '+media', root_to_media, INF)]
    views = [(MediaFile, '+index', MediaFileView)]
    public_views = [(MediaFile, '+index', MediaFileView)]
