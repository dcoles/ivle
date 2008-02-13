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

from common import util
from common import interpret
from os import path
import os
import urlparse
import re

def handle(req):
    """
    Handler for the Forum application.
    
    This application implements a general purpose PHP CGI loader
    """
    
    # Settings
    #forum_base = "/var/www/default/smf"
    forum_base = "php/phpBB3"
    #default_page = "index.php"

    # Set request attributes

    # These files don't really exist - just a test of our linking
    # capabilities
    #req.styles = ["media/dummy/dummy.css"]
    #req.scripts = ["media/dummy/dummy.js", "media/dummy/hello.js"]
    
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

    
    #req.write(framequery + '\n')

    # If the tail of the forum url is empty or a known special request
    # then wrap the page in the headers and footer and load the default or
    # special page in the ivlebody frame
    location = req.path
    if board or topic:
        location = forum_page + framequery
    
    frameurl = util.make_path(path.join(forum_base,location))
    req.content_type = "text/html"
    req.write_html_head_foot = True
    req.write('<object' +
              ' id="ivlebody"' +
              ' style="top:0"' +
              ' type="text/html"' +
              ' data="' + frameurl + framequery + '"' +
              '/>\n'
    )
    # Otherwise serve the page without the wrapper
    #else:
    #    req.write(req.path)
    #    req.throw_error(req.HTTP_BAD_REQUEST)



        # Let the Server determine the MIME type
    #    req.content_type = ""

        # Don't write header or footer - we can't tell if it's HTML or 
        # something else like an image
    #    req.write_html_head_foot = False

        # Do some basic dispatch, if it ends in .php interpret with php-cgi
    #    if re.search('\.php$',hierarchical_part,re.IGNORECASE):
    #        interpret.execute_cgi(
    #            ['/usr/bin/php5-cgi'],
    #            forum_base,
    #            req
    #        )
        # Otherwise just ship the file directly
    #    else:
            #req.content_type = "application/x-httpd-php"
    #        file_path = os.path.join(forum_base, req.path)
    #        if os.access(file_path,os.R_OK):
    #            req.sendfile(path.join(forum_base, req.path))
            # If we can't read the file, throw HTTP Error
    #        else:
    #            req.throw_error(req.HTTP_BAD_REQUEST)
   
