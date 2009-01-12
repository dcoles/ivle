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

import os.path

import conf
import fileservice_lib
import common
import common.interpret
import common.util

# handle_with_trampoline controls the way in which fileservice_lib is invoked.
# If False, it will simply be called directly by this handler.
# If True, the request will get marshalled into a CGI environment and the
# trampoline will invoke services/fileservices within the user's jail
# (SetUID'd to them). This script will then wrap the CGI environment in a
# replica of the original environment and handle it that way.
# This is a lot of overhead but it's the only way to properly ensure we are
# acting "as" that user and therefore we don't run into permissions problems.
# If set to True, it will be a lot more efficient, but there will be
# permissions issues unless all user's files are owned by the web server user.
HANDLE_WITH_TRAMPOLINE = True

fileservice_path = "/opt/ivle/services/fileservice"   # Within jail

def handle(req):
    """Handler for the File Services application."""
    if len(req.path) == 0:
        # If no path specified, default to the user's home directory
        req.throw_redirect(common.util.make_path(os.path.join('fileservice',
                                                       req.user.login)))
    if not HANDLE_WITH_TRAMPOLINE:
        fileservice_lib.handle(req)
    else:
        interp_object = common.interpret.interpreter_objects["cgi-python"]
        user_jail_dir = os.path.join(conf.jail_base, req.user.login)
        common.interpret.interpret_file(req, req.user.login, user_jail_dir,
            fileservice_path, interp_object, gentle=False)
