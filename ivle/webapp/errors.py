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

# Author: Will Grant

class HTTPError(Exception):
    '''A base class for all HTTP errors.'''

class BadRequest(HTTPError):
    codename = 'Bad Request'
    code = 400

class Unauthorized(HTTPError):
    codename = 'Unauthorized'
    code = 401

class Forbidden(HTTPError):
    codename = 'Forbidden'
    code = 403

class NotFound(HTTPError):
    codename = 'Not Found'
    code = 404

class MethodNotAllowed(HTTPError):
    def __init__(self, allowed, *args, **kwargs):
        self.allowed = allowed
        super(HTTPError, self).__init__(*args, **kwargs)

    codename = 'Method Not Allowed'
    code = 405
