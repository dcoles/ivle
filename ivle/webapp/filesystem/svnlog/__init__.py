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

# Author: William Grant

import os

import cjson
import pysvn

import ivle.date
import ivle.interpret
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.errors import NotFound, BadRequest
from ivle.webapp.filesystem import make_path_segments

class SubversionLogView(XHTMLView):
    template = 'template.html'
    tab = 'files'

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['log.css']

        svnlogservice_path = os.path.join(req.config['paths']['share'],
                                          'services/svnlogservice')

        user_jail_dir = os.path.join(req.config['paths']['jails']['mounts'],
                                     req.user.login)
        (out, err) = ivle.interpret.execute_raw(req.user, user_jail_dir,
                             '/home', svnlogservice_path, [self.path])
        assert not err

        response = cjson.decode(out)
        if 'error' in response:
            if response['error'] == 'notfound':
                raise NotFound()
            else:
                raise AssertionError('Unknown error from svnlogservice: %s' %
                                     response['error'])

        # No error. We must be safe.
        ctx['path'] = self.path
        ctx['url'] = req.make_path(os.path.join('svnlog', self.path))
        ctx['diffurl'] = req.make_path(os.path.join('diff', self.path))
        ctx['title'] = self.path.rsplit('/', 1)[-1]
        ctx['paths'] = make_path_segments(self.path)

        sr = ivle.svn.revision_from_string(
                   req.get_fieldstorage().getfirst("r"))
        ctx['revno'] = sr.number if sr and \
                       sr.kind == pysvn.opt_revision_kind.number else None
        ctx['logs'] = response['logs']

        # Create URLs for each of the versioned files.
        # XXX: This scheme only works for stuff/!
        for log in ctx['logs']:
            log['date'] = ivle.date.make_date_nice(log['date'])
            for pathaction in log['paths']:
                pathaction.append(req.make_path(os.path.join('files',
                                  ivle.util.split_path(req.path)[0],
                                  pathaction[0][1:])) + '?r=%d' % log['revno'])

class Plugin(ViewPlugin, MediaPlugin):
    urls = [
        ('/svnlog', SubversionLogView, {'path': ''}),
        ('/svnlog/*path', SubversionLogView),
    ]

    media = 'media'
