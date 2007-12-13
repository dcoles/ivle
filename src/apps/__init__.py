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

# Module: apps
# Author: Matt Giuca
# Date: 12/12/2007

# Loads IVLE applications.
# All sub-packages in this package are apps.

from mod_python import apache

def call_app(appname, req):
    """Calls an application with the given name. Passes req to the app's
    handler."""
    try:
        # level=-1 to make it look in the right directory
        app_module = __import__(appname, globals(), locals(), [], -1)
        app_module.handle(req)
    except ImportError:
        # Any problems meant it's a server error, because conf/apps.py said
        # this app would be here.
        raise apache.SERVER_RETURN, apache.HTTP_INTERNAL_SERVER_ERROR
