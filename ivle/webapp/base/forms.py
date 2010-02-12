# IVLE
# Copyright (C) 2010 The University of Melbourne
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

import formencode
from genshi.filters import HTMLFormFiller

from ivle.webapp.base.xhtml import XHTMLView

class BaseFormView(XHTMLView):
    """A base form view."""

    def filter(self, stream, ctx):
        return stream | HTMLFormFiller(data=ctx['data'])

    def populate_state(self, state):
        pass

    def get_return_url(self, obj):
        return self.req.publisher.generate(obj)

    def get_default_data(self, req):
        raise NotImplementedError()

    def save_object(self, req, data):
        raise NotImplementedError()

    @property
    def validator(self):
        raise NotImplementedError()

    def populate(self, req, ctx):
        if req.method == 'POST':
            data = dict(req.get_fieldstorage())
            try:
                self.populate_state(req)
                data = self.validator.to_python(data, state=req)

                obj = self.save_object(req, data)

                req.store.commit()
                req.throw_redirect(self.get_return_url(obj))
            except formencode.Invalid, e:
                error_value = e.msg
                errors = e.unpack_errors()
        else:
            data = self.get_default_data(req)
            error_value = None
            errors = {}

        if errors:
            req.store.rollback()

        ctx['req'] = req
        ctx['context'] = self.context
        ctx['data'] = data or {}
        ctx['errors'] = errors
        # If all of the fields validated, set the global form error.
        if isinstance(errors, basestring):
            ctx['error_value'] = errors


