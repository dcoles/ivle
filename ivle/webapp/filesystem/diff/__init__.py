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

'''Components of the webapp for diffing user files.'''

import os
import re
import cgi

try:
    import json
except ImportError:
    import simplejson as json

import genshi

import ivle.interpret
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.errors import NotFound, BadRequest
from ivle.webapp.filesystem import make_path_breadcrumbs
from ivle.webapp import ApplicationRoot

class DiffView(XHTMLView):
    '''A view to present a nice XHTML Subversion diff from a user's jail.'''
    template = 'template.html'
    tab = 'files'
    breadcrumb_text = 'Files'

    subpath_allowed = True

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['diff.css']

        revfields = req.get_fieldstorage().getlist("r")
        if len(revfields) > 2:
            raise BadRequest('A maximum of two revisions can be given.')

        revs = [revfield.value for revfield in revfields]

        jail_dir = os.path.join(req.config['paths']['jails']['mounts'],
                                req.user.login)
        (out, err) = ivle.interpret.execute_raw(req.config, req.user, jail_dir,
                            '/home', os.path.join(req.config['paths']['share'],
                                                  'services/diffservice'),
                            [self.path] + revs
                            )
        assert not err

        response = json.loads(out)
        if 'error' in response:
            if response['error'] == 'notfound':
                raise NotFound()
            else:
                raise AssertionError('Unknown error from diffservice: %s' %
                                     response['error'])

        # No error. We must be safe.
        diff = response['diff']

        # Split up the udiff into individual files
        diff_matcher = re.compile(
            r'^Index: (.*)\n\=+\n((?:[^I].*\n)*)',re.MULTILINE
        )

        ctx['title'] = os.path.normpath(self.path).rsplit('/', 1)[-1]
        self.extra_breadcrumbs = make_path_breadcrumbs(req, self.subpath)
        self.extra_breadcrumbs.append(SubversionDiffBreadcrumb())

        # Create a dict with (name, HTMLdiff) pairs for each non-empty diff.
        ctx['files'] = dict([(fd[0], genshi.XML(htmlfy_diff(fd[1])))
                             for fd in diff_matcher.findall(diff)
                             if fd[1]])

    @property
    def path(self):
        return os.path.join(*self.subpath) if self.subpath else ''


class SubversionDiffBreadcrumb(object):
    text = 'Subversion Diff'


def htmlfy_diff(difftext):
    """Adds HTML markup to a udiff string"""
    output = cgi.escape(difftext)
    subs = {
     r'^([\+\-]{3})\s(\S+)\s\((.+)\)$':
         r'<span class="diff-files">\1 \2 <em>(\3)</em></span>',
     r'^\@\@ (.*) \@\@$':
         r'<span class="diff-range">@@ \1 @@</span>',
     r'^\+(.*)$':
         r'<span class="diff-add">+\1</span>',
     r'^\-(.*)$':
         r'<span class="diff-sub">-\1</span>',
     r'^\\(.*)$':
         r'<span class="diff-special">\\\1</span>'
    }

    for match in subs:
        output = re.compile(match, re.MULTILINE).sub(subs[match], output)

    return '<pre class="diff">%s</pre>' % output

class Plugin(ViewPlugin, MediaPlugin):
    views = [(ApplicationRoot, 'diff', DiffView)]

    media = 'media'
