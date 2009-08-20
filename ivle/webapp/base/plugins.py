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

    View plugins have three main types of registration:
     - forward_routes: A list of traversals from objects to their
       descendants. The discriminator is the source class and a list of zero
       or more intermediate path segments. An optional argument count may be
       given -- arguments will be taken from the path after the intermediate
       segments. The specified callable will be given the source object and
       any arguments, and should return the target object.

     - reverse_routes: A list of traversals from objects to their parents.
       The discriminator is just the child class. The provided callable must
       return a tuple of (parent_object, ('intermediate', path', 'segments')).

     - views: A list of named views for objects. The discriminator is the
       context object class, view name, and an optional view set. An optional
       (possibly infinite) argument count may again be given. The arguments
       values will be taken from the path after the view name. The callable
       should take the request object, target object and subpath, and return
       a view object.

    See ivle.dispatch.generate_publisher for the registry code.

    View plugins may also have a 'help' property, which should contain a dict
    of dicts and help file names. This dict is then used to generate the
    appropriate entries in the help system.

    Tabs can also be defined by view plugins. To define tabs, provide a 'tabs'
    property containing 6-tuples of (name, title, desc, icon, path, weight).
    The icon should be relative to the plugin's media directory, and the path
    should be relative to the root. The weight is used for ordering; larger
    weights are further right.
    """
    pass

class PublicViewPlugin(BasePlugin):
    """Marker class for plugins that provide public mode views.

    Public view plugins can specify the same 'urls' property as normal view
    plugins, but they are added to the public mode publisher instead.
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
