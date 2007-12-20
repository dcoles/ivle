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

# Module: dispatch_handler
# Author: Matt Giuca
# Date: 11/12/2007

# This is a mod_python handler program. The correct way to call it is to have
# Apache send all requests to be handled by the module 'dispatch'.

# This file is a wrapper around the dispatch module, necessary because
# mod_python does not (for some reason) load the handler directory into
# sys.path.
# It requires that the server config has the following line:
# PythonOption ivle.handlerpath "PATH-TO-IVLE"

# Sets sys.path with the correct path, then calls the handler in the dispatch
# module.

import sys
from mod_python import apache

def handler(req):
    # A nasty hack :(
    # The Apache httpd.conf needs to specify ivle.handlerpath as an option
    # (see README).

    try:
        handlerpath = req.get_options()['ivle.handlerpath']
        if handlerpath not in sys.path:
            sys.path.append(handlerpath)
        import dispatch
        import conf
        return dispatch.handler(req)
    except KeyError:
        # Note: "Internal Server Error" if "ivle.handlerpath" is not set
        # (this is valid as it reflects an error in the Apache config
        # But give useful feedback in debug mode
        raise Exception("Missing configuration option 'ivle.handlerpath'")
