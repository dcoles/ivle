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

# Module: authenticate
# Author: Matt Giuca
# Date:   21/12/2007

# Provides a mechanism for authenticating a username and password, and
# returning a yes/no response.

def authenticate(username, password):
    """Determines whether a particular username/password combination is
    valid. Returns True or False. The password is in cleartext."""

    # WARNING: Both username and password may contain any characters, and must
    # be sanitized within this function.
    # TEMP: Just a hardcoded login
    return username == 'user' and password == 'pass'
