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

class HTTPError(Exception):
    '''A base class for all HTTP errors.'''
    message = None

    def __init__(self, message=None):
        # Only override the builtin one if it's actually specified.
        if message:
            self.message = message

class BadRequest(HTTPError):
    codename = 'Bad Request'
    message = 'Your browser sent a request that IVLE did not understand.'
    code = 400

class Unauthorized(HTTPError):
    codename = 'Unauthorized'
    message = 'You are not allowed to view this part of IVLE.'
    code = 401

class Forbidden(HTTPError):
    codename = 'Forbidden'
    message = 'You are not allowed to view this part of IVLE.'
    code = 403

class NotFound(HTTPError):
    codename = 'Not Found'
    message = 'The requested path does not exist.'
    code = 404

class MethodNotAllowed(HTTPError):
    def __init__(self, allowed, *args, **kwargs):
        self.allowed = allowed
        super(HTTPError, self).__init__(*args, **kwargs)

    codename = 'Method Not Allowed'
    message = '''Your browser sent a request to IVLE using the wrong method.
This is probably a bug in IVLE; please report it to the administrators.'''
    code = 405
