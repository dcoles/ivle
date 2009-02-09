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
    """
    pass
    
class OverlayPlugin(BasePlugin):
    """
    Marker class for plugins which provide overlays.
    
    Overlay plugins provide mini-views which can be displayed on top of other
    views. The canonical example of a plugin of this type is the Console plugin.
    """
    pass
