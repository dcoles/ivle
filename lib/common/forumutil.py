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

# Module: forumutil
# Author: David Coles
# Date: 18/02/2008

# Forum Utilities for communicating with the Forum

import hashlib
import time
from mod_python import Cookie
from urllib import quote

cookie_name = 'ivleforumcookie'

def make_forum_cookie(login_details):
    secret = "VERYSECRET"

    login = quote(login_details.login)
    nick = quote(login_details.nick)
    email = ''
    if login_details.email != None:
        email = quote(login_details.email)


    role = quote(str(login_details.role))
    
    hashtext = login + nick + email + role + secret
    hash = hashlib.md5(hashtext).hexdigest()
    data = quote(login + ':' + nick + ':' + email + ':' + role + ':' + hash)

    return Cookie.Cookie(cookie_name,data,expires=time.time()+86400,path='/')
 
def invalidated_forum_cookie():
    return Cookie.Cookie(cookie_name,'NONE',expires=time.time()+86400,path='/')
