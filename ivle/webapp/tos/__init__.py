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

import ivle.util
import ivle.webapp.security
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin

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
        ctx['text'] = ivle.util.get_terms_of_service()

        if self.mode == 'accept':
            self.plugin_scripts[Plugin] = ['tos.js']
            ctx['user'] = self.user

class Plugin(ViewPlugin, MediaPlugin):
    """Registration for the Terms of Service plugin."""
    urls = [
        ('+tos', TermsOfServiceView),
    ]

    media = 'media'
