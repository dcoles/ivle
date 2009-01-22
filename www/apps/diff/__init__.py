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

# App: Diff Service
# Author: David Coles
# Date: 21/2/2008

# This app is a wrapper around the diff script run through the trampoline

import os.path

import ivle.conf
import ivle.interpret


# handle_with_trampoline controls the way in which fileservice_lib is invoked.
# If False, it will simply be called directly by this handler.
# If True, the request will get marshalled into a CGI environment and the
# trampoline will invoke services/fileservices within the user's jail (SetUID'd
# to them). This script will then wrap the CGI environment in a replica of the
# original environment and handle it that way.
# This is a lot of overhead but it's the only way to properly ensure we are
# acting "as" that user and therefore we don't run into permissions problems.
# If set to True, it will be a lot more efficient, but there will be
# permissions issues unless all user's files are owned by the web server user.
HANDLE_WITH_TRAMPOLINE = True

diffservice_path = os.path.join(ivle.conf.share_path, 'services/diffservice')

def handle(req):
    """Handler for the File Services application."""
    req.styles = ["media/diff/diff.css"] # CSS styles
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Handle
    if not HANDLE_WITH_TRAMPOLINE:
        pass
    else:
        if req.path == "":
            req.throw_redirect(os.path.join(req.uri,req.user.login));
        interp_object = ivle.interpret.interpreter_objects["cgi-python"]
        user_jail_dir = os.path.join(ivle.conf.jail_base, req.user.login)
        ivle.interpret.interpret_file(req, req.user, user_jail_dir,
            diffservice_path, interp_object)

