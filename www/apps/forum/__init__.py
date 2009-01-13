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

# App: Forum
# Author: David Coles
# Date: 12/02/2008

# This is an IVLE application.
# A SMF forum application for IVLE.

import os
import urlparse
import re

from ivle import util
from ivle import interpret

def handle(req):
    """
    Handler for the Forum application.
    
    This application implements a general purpose PHP CGI loader
    """
    
    # Settings

    forum_base = "php/phpBB3"

    # Set request attributes

    req.styles = ["media/forum/forum.css"]
    
    # Process URL for special directives
    url = urlparse.urlparse(req.path)
    hierarchical_part = url[2]

    forum_page = "" # use the default forum page
    framequery = "?"

    board = re.match('board/(.*?)(/|$)',hierarchical_part)
    if board:
        framequery += 'f=' + board.group(1) + "&"
        forum_page = "viewforum.php"

    topic = re.search('topic/(.*?)(/|$)',hierarchical_part)
    if topic:
        framequery += 't=' + topic.group(1)
        forum_page = "viewtopic.php"
   
    # If the tail of the forum url is empty or a known special request
    # then wrap the page in the headers and footer and load the default or
    # special page in the ivlebody frame
    location = req.path
    if board or topic:
        location = forum_page + framequery
    
    frameurl = util.make_path(os.path.join(forum_base,location))
    req.content_type = "text/html"
    req.write_html_head_foot = True
    req.write('<object class="fullscreen" type="text/html" data="%s">'%
        (frameurl + framequery))
