# IVLE
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

import os.path

from ivle.database import Subject
from ivle.webapp.media import MediaFileView
from ivle.webapp.publisher import INF
from ivle.webapp.publisher.decorators import forward_route


class SubjectMediaFile(object):
    """A subject content media file.

    Subject media can be dropped in
    /var/lib/ivle/content/subjects/$shortname/media,
    and will be served up at http://.../subjects/$shortname/+media.
    """

    def __init__(self, context, path):
        self.context = context
        self.path = path
        self.version = None

    @property
    def filename(self):
        """Calculate just the path under the subject content directory.

        The view will work out the rest of the path from the config.
        """
        subjectdir = os.path.join(self.context.short_name, 'media')
        return os.path.join(subjectdir, self.path)

    def get_permissions(self, user, config):
        return self.context.get_permissions(user, config)


class SubjectMediaView(MediaFileView):
    '''The view of subject media files.

    URIs pointing here will just be served directly, from the subject's
    media directory.
    '''
    permission = 'view'

    def get_filename(self, req):
        return os.path.join(
            req.config['paths']['data'],
            'content/subjects', self.context.filename)

    def get_permissions(self, user, config):
        return self.context.get_permissions(user, config)


@forward_route(Subject, '+media', argc=INF)
def subject_to_media(subject, *segments):
    path = os.path.normpath(os.path.join(*segments))

    return SubjectMediaFile(subject, path)

