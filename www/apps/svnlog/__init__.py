# IVLE
# Copyright (C) 2008 The University of Melbourne
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

# App: SVN Log Service
# Author: William Grant
# Date: 08/07/2008

# This is merely a wrapper around the trampolined svnlogservice.

import os

import conf
import common.interpret

def handle(req):
    """Handler for Subversion log functionality."""
    req.styles = ["media/svn/log.css"]
    req.write_html_head_foot = True

    if req.path == "":
        req.throw_redirect(os.path.join(req.uri, req.user.login))
    interpreter = common.interpret.interpreter_objects["cgi-python"]
    jail_dir = os.path.join(conf.jail_base, req.user.login)
    common.interpret.interpret_file(req, req.user.login, jail_dir,
          '/opt/ivle/services/svnlogservice', interpreter)

