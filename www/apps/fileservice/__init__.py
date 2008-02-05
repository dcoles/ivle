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

# App: File Service (AJAX server)
# Author: Matt Giuca
# Date: 9/1/2008

# This application is a wrapper around the library module fileservice.
# It can be configured to either call the library directly (in which case it
# behaves just like a regular application), or run it through the trampoline
# as a CGI app.

# It receives file handling instructions as requests. Performs actions on the
# student's workspace, and returns directory listings in JSON.

# See the documentation in lib/fileservice for details.

import fileservice_lib

def handle(req):
    """Handler for the File Services application."""
    fileservice_lib.handle(req)
