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

import re
import datetime

import formencode
import formencode.validators
from genshi.filters import HTMLFormFiller

from ivle.webapp.base.xhtml import XHTMLView


class BaseFormView(XHTMLView):
    """A base form view."""

    @property
    def validator(self):
        """The FormEncode validator to use.

        The request will be passed in as state, after potentially being
        modified by populate_state().
        """
        raise NotImplementedError()

    def populate_state(self, state):
        """Populate the state given to the FormEncode validator.

        Subclasses can override this and set additional attributes.
        """
        pass

    def get_return_url(self, obj):
        """Return the URL to which the completed form should redirect.

        By default this will redirect to the saved object.
        """
        return self.req.publisher.generate(obj)

    def get_default_data(self, req):
        """Return a dict mapping field names to default form values.

        For an edit form, this should return the object's existing data.
        For a creation form, this should probably return an empty dict.

        This must be overridden by subclasses.
        """
        raise NotImplementedError()

    def save_object(self, req, data):
        """Take the validated form data and turn it into an object.

        The object must then be returned.

        For an edit form, this should just overwrite data on an existing
        object.
        For a creation form, this should create a new object with the given
        data and add it to the request's store.
        """
        raise NotImplementedError()

    def filter(self, stream, ctx):
        return stream | HTMLFormFiller(data=ctx['data'])

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


VALID_URL_NAME = re.compile(r'^[a-z0-9][a-z0-9_\+\.\-]*$')


class URLNameValidator(formencode.validators.UnicodeString):
    def validate_python(self, value, state):
        super(URLNameValidator, self).validate_python(value, state)
        if not VALID_URL_NAME.match(value):
            raise formencode.Invalid(
                'Must consist of a lowercase alphanumeric character followed '
                'by any number of lowercase alphanumerics, ., +, - or _.',
                value, state)

class DateTimeValidator(formencode.validators.FancyValidator):
    """Accepts a date/time in YYYY-MM-DD HH:MM:SS format. Converts to a
    datetime.datetime object."""
    def _to_python(self, value, state):
        """Validate and convert."""
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError, e:
            raise formencode.Invalid(str(e) + " -> " + repr(value), value, state)
            raise formencode.Invalid("Must be a timestamp in "
                "YYYY-MM-DD HH:MM:SS format", value, state)
    def _from_python(self, value, state):
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except AttributeError:
            raise formencode.Invalid("Must be a datetime.datetime object")
