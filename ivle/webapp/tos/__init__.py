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

# Author: Matt Giuca, Will Grant

"""View to display the Terms of Service.

This is mainly for the benefit of the link in ivle.webapp.help."""

import os.path

import ivle.webapp.security
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin

def get_terms_of_service(config):
    """
    Sends the Terms of Service document to the req object.
    This consults conf to find out where the TOS is located on disk, and sends
    that. If it isn't found, it sends a generic message explaining to admins
    how to create a real one.
    """
    try:
        return open(os.path.join(config['paths']['data'],
                    'notices/tos.html')).read()
    except IOError:
        return """\
<p><b>*** SAMPLE ONLY ***</b></p>
<p>This is the text of the IVLE Terms of Service.</p>
<p>The administrator should create a license file with an appropriate
"Terms of Service" license for your organisation.</p>
<h2>Instructions for Administrators</h2>
<p>You are seeing this message because you have not configured a Terms of
Service document.</p>
<p>When you configured IVLE, you specified a path to the Terms of Service
document (this is found in <b><tt>ivle/conf/conf.py</tt></b> under
"<tt>tos_path</tt>").</p>
<p>Create a file at this location; an HTML file with the appropriately-worded
license.</p>
<p>This should be a normal XHTML file, except it should not contain
<tt>html</tt>, <tt>head</tt> or <tt>body</tt> elements - it should
just be the contents of a body element (IVLE will wrap it accordingly).</p>
<p>This will automatically be used as the license text instead of this
placeholder text.</p>
"""

class TermsOfServiceView(XHTMLView):
    """View of the Terms of Service, allowing acceptance.

    Users with state 'no_agreement' see buttons to accept or decline.
    If a user has already accepted it, they just see a static page.
    """

    allow_overlays = False

    def __init__(self, req):
        # We need to be able to handle the case where a user has status
        # 'no_agreement'. In that case, req.user will be None, so we have
        # to get it ourselves.
        if req.user is None:
            self.user = ivle.webapp.security.get_user_details(req)
            self.mode = 'accept'
            self.template = 'accept.html'
        else:
            self.user = req.user
            self.mode = 'view'
            self.template = 'view.html'

    def authorize(self, req):
        # This can be used by any authenticated user, even if they haven't
        # accepted the ToS yet.
        return ivle.webapp.security.get_user_details(req) is not None

    def populate(self, req, ctx):
        ctx['text'] = get_terms_of_service(req.config)

        if self.mode == 'accept':
            self.plugin_scripts[Plugin] = ['tos.js']
            ctx['user'] = self.user

class Plugin(ViewPlugin, MediaPlugin):
    """Registration for the Terms of Service plugin."""
    urls = [
        ('+tos', TermsOfServiceView),
    ]

    media = 'media'
