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

# Module: dispatch
# Author: Matt Giuca
# Date: 11/12/2007

# This is a mod_python handler program. The correct way to call it is to have
# Apache send all requests to be handled by the module 'dispatch'.

# Top-level handler. Handles all requests to all pages in IVLE.
# Handles authentication (not authorization).
# Then passes the request along to the appropriate ivle app.

from mod_python import apache

def handler(req):
    # TEMP: Dummy (test) handler
    req.content_type = "text/plain"
    req.write("Hello, IVLE!\n")
    req.write(str(req.uri))
    return apache.OK

