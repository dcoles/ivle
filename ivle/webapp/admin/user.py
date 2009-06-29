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

import formencode
import formencode.validators
from genshi.filters import HTMLFormFiller

from ivle.webapp.base.rest import JSONRESTView, require_permission
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.errors import NotFound, Unauthorized
import ivle.database
import ivle.util

# List of fields returned as part of the user JSON dictionary
# (as returned by the get_user action)
user_fields_list = (
    "login", "state", "unixid", "email", "nick", "fullname",
    "admin", "studentid", "acct_exp", "pass_exp", "last_login",
    "svn_pass"
)

class UserRESTView(JSONRESTView):
    """
    A REST interface to the user object.
    """
    def __init__(self, req, login):
        super(UserRESTView, self).__init__(self, req, login)
        self.context = ivle.database.User.get_by_login(req.store, login)
        if self.context is None:
            raise NotFound()

    @require_permission('view')
    def GET(self, req):
        # XXX Check Caps
        user = ivle.util.object_to_dict(user_fields_list, self.context)
        # Convert time stamps to nice strings
        for k in 'pass_exp', 'acct_exp', 'last_login':
            if user[k] is not None:
                user[k] = unicode(user[k])

        user['local_password'] = self.context.passhash is not None
        return user

class UserSettingsView(XHTMLView):
    template = 'templates/user-settings.html'
    tab = 'settings'
    permission = 'edit'

    def __init__(self, req, login):
        self.context = ivle.database.User.get_by_login(req.store, login)
        if self.context is None:
            raise NotFound()

    def populate(self, req, ctx):
        self.plugin_scripts[Plugin] = ['settings.js']
        self.scripts_init = ['revert_settings']

        ctx['login'] = self.context.login

class UserEditSchema(formencode.Schema):
    nick = formencode.validators.UnicodeString(not_empty=True)
    email = formencode.validators.Email(not_empty=False,
                                        if_missing=None)

class UserEditView(XHTMLView):
    """A form to change a user's details."""
    template = 'templates/user-edit.html'
    tab = 'settings'
    permission = 'edit'

    def __init__(self, req, login):
        self.context = ivle.database.User.get_by_login(req.store, login)
        if self.context is None:
            raise NotFound()

    def filter(self, stream, ctx):
        return stream | HTMLFormFiller(data=ctx['data'])

    def populate(self, req, ctx):
        if req.method == 'POST':
            data = dict(req.get_fieldstorage())
            try:
                validator = UserEditSchema()
                data = validator.to_python(data, state=req)
                self.context.nick = data['nick']
                self.context.email = unicode(data['email']) if data['email'] \
                                     else None
                req.store.commit()
                req.throw_redirect(req.uri)
            except formencode.Invalid, e:
                errors = e.unpack_errors()
        else:
            data = {'nick': self.context.nick,
                    'email': self.context.email
                   }
            errors = {}

        ctx['user'] = self.context
        ctx['data'] = data
        ctx['offering'] = self.context
        ctx['errors'] = errors

class Plugin(ViewPlugin, MediaPlugin):
    """
    The Plugin class for the user plugin.
    """
    # Magic attribute: urls
    # Sequence of pairs/triples of
    # (regex str, handler class, kwargs dict)
    # The kwargs dict is passed to the __init__ of the view object
    urls = [
        ('~:login/+settings', UserSettingsView),
        ('~:login/+edit', UserEditView),
        ('api/~:login', UserRESTView),
    ]

    media = 'user-media'
