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

# Author: David Coles, Will Grant

import os
import re
import time
import hashlib
import urlparse
from urllib import quote

from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, CookiePlugin, MediaPlugin
import ivle.util
import ivle.config

class ForumView(XHTMLView):
    appname = 'forum'

    def __init__(self, req, path):
        self.path = path

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['forum.css']

        forum_base = "php/phpBB3"

        ctx['url'] = ivle.util.make_path(os.path.join(forum_base, self.path))

class ForumBoardView(ForumView):
    def __init__(self, req, board):
        self.path = 'viewforum.php?f=' + board

class ForumTopicView(ForumView):
    def __init__(self, req, topic):
        self.path = 'viewtopic.php?t=' + topic

def make_forum_cookie(user):
    secret = ivle.config.Config().plugin_configs[Plugin]['secret']

    login = quote(user.login)
    nick = quote(user.nick)
    email = ''
    if user.email != None:
        email = quote(user.email)

    role = quote(str(user.role))

    hashtext = login + nick + email + role + secret
    hash = hashlib.md5(hashtext).hexdigest()
    data = quote(login + ':' + nick + ':' + email + ':' + role + ':' + hash)

    return data

class Plugin(ViewPlugin, CookiePlugin, MediaPlugin):
    urls = [
        ('forum', ForumView, {'path': ''}),
        ('forum/+board/:board', ForumBoardView),
        ('forum/+topic/:topic', ForumTopicView),
        ('forum/*path', ForumView),
    ]

    tabs = [
        ('forum', 'Forum', 'Discussion boards for material relating to '
         'Informatics, IVLE and Python.', 'forum.png', 'forum', 4)
    ]

    cookies = {'ivleforumcookie': make_forum_cookie}

    media = 'media'
