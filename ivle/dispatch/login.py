# IVLE - Informatics Virtual Learning Environment
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

# Module: dispatch.login
# Author: Matt Giuca
# Date: 21/12/2007

import ivle.database

def get_user_details(req):
    """Gets the name of the logged in user, without presenting a login box
    or attempting to authenticate.
    Returns None if there is no user logged in.
    """
    session = req.get_session()

    # Check the session to see if someone is logged in. If so, go with it.
    try:
        login = session['login']
    except KeyError:
        return None

    # Get the full User object from the db associated with this login
    return ivle.database.User.get_by_login(req.store, login)
