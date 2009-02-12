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

class BasePlugin(object):
    """
    Base class for all Plugin classes.
    """
    pass
    
class ViewPlugin(BasePlugin):
    """Marker class for plugins that provide views.
    
    View plugins must have a 'urls' property which contains an iterable of pairs
    or triples, like (routex string, handler class, kwargs dict). The kwargs
    dict is optional. If present, the members of the kwargs dict will be passed
    as keyword arguments to the constructor of the view object.
    
    View plugins may also have a 'help' property, which should contain a dict
    of dicts and help file names. This dict is then used to generate the
    appropriate entries in the help system.
    """
    pass
    
class OverlayPlugin(BasePlugin):
    """Marker class for plugins which provide overlays.
    
    Overlay plugins provide mini-views which can be displayed on top of other
    views. The canonical example of a plugin of this type is the Console plugin.
    """
    pass

class CookiePlugin(BasePlugin):
    """Marker class for plugins which provide cookies.

    Cookie plugins provide a 'cookies' dict mapping names to generation
    functions. The function should return the data to store in the cookie on
    login. If the function is None, the cookie is not created on login, just
    deleted on logout.
    """
    pass

class MediaPlugin(BasePlugin):
    """Marker class for plugins which provide media files.

    Media plugins provide a 'media' attribute, which is a string pointing to a
    subdirectory that contains media files to be served statically.
    """
    pass
