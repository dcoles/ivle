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

from ivle.webapp import ApplicationRoot
from ivle.webapp.base.forms import BaseFormView
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.admin.publishing import root_to_user, user_url
from ivle.database import User
import ivle.date


class UsersView(XHTMLView):
    """A list of all IVLE users."""
    template = 'templates/users.html'
    tab = 'users'
    breadcrumb_text = 'Users'

    def authorize(self, req):
        return req.user and req.user.admin

    def populate(self, req, ctx):
        ctx['req'] = req
        ctx['users'] = req.store.find(User).order_by(User.login)


class UserEditSchema(formencode.Schema):
    nick = formencode.validators.UnicodeString(not_empty=True)
    email = formencode.validators.Email(not_empty=False,
                                        if_missing=None)

class UserEditView(BaseFormView):
    """A form to change a user's details."""
    template = 'templates/user-edit.html'
    tab = 'users'
    permission = 'edit'

    @property
    def validator(self):
        return UserEditSchema()

    def get_default_data(self, req):
        return {'nick': self.context.nick,
                'email': self.context.email
                }

    def save_object(self, req, data):
        self.context.nick = data['nick']
        self.context.email = unicode(data['email']) if data['email'] \
                             else None
        return self.context

    def populate(self, req, ctx):
        super(UserEditView, self).populate(req, ctx)
        ctx['format_datetime'] = ivle.date.make_date_nice
        ctx['format_datetime_short'] = ivle.date.format_datetime_for_paragraph


class UserAdminSchema(formencode.Schema):
    admin = formencode.validators.StringBoolean(if_missing=False)
    disabled = formencode.validators.StringBoolean(if_missing=False)
    fullname = formencode.validators.UnicodeString(not_empty=True)
    studentid = formencode.validators.UnicodeString(not_empty=False,
                                                    if_missing=None
                                                    )

class UserAdminView(BaseFormView):
    """A form for admins to change more of a user's details."""
    template = 'templates/user-admin.html'
    tab = 'users'

    def authorize(self, req):
        """Only allow access if the requesting user is an admin."""
        return req.user and req.user.admin

    @property
    def validator(self):
        return UserAdminSchema()

    def get_default_data(self, req):
        return {'admin': self.context.admin,
                'disabled': self.context.state == u'disabled',
                'fullname': self.context.fullname,
                'studentid': self.context.studentid,
                }

    def save_object(self, req, data):
        if self.context is req.user:
            # Admin checkbox is disabled -- assume unchanged
            data['admin'] = self.context.admin
            data['disabled'] = self.context.state == u'disabled'
        else:
            self.context.admin = data['admin']
            if self.context.state in (u'enabled', u'disabled'):
                self.context.state = (u'disabled' if data['disabled']
                        else u'enabled')
        self.context.fullname = data['fullname'] \
                                if data['fullname'] else None
        self.context.studentid = data['studentid'] \
                                 if data['studentid'] else None
        return self.context

    def populate(self, req, ctx):
        super(UserAdminView, self).populate(req, ctx)

        # Disable the admin checkbox if editing oneself
        ctx['disable_admin'] = self.context is req.user

class PasswordChangeView(XHTMLView):
    """A form to change a user's password, with knowledge of the old one."""
    template = 'templates/user-password-change.html'
    tab = 'users'
    permission = 'edit'

    def authorize(self, req):
        """Only allow access if the requesting user holds the permission,
           and the target user has a password set. Otherwise we might be
           clobbering external authn.
        """
        return super(PasswordChangeView, self).authorize(req) and \
               self.context.passhash is not None

    def populate(self, req, ctx):
        error = None
        if req.method == 'POST':
            data = dict(req.get_fieldstorage())
            if data.get('old_password') is None or \
               not self.context.authenticate(data.get('old_password')):
                error = 'Incorrect password.'
            elif data.get('new_password') != data.get('new_password_again'):
                error = 'New passwords do not match.'
            elif not data.get('new_password'):
                error = 'New password cannot be empty.'
            else:
                self.context.password = data['new_password']
                req.store.commit()
                req.throw_redirect(req.uri)

        ctx['req'] = req
        ctx['user'] = self.context
        ctx['error'] = error

class PasswordResetView(XHTMLView):
    """A form to reset a user's password, without knowledge of the old one."""
    template = 'templates/user-password-reset.html'
    tab = 'users'

    def authorize(self, req):
        """Only allow access if the requesting user is an admin."""
        return req.user and req.user.admin

    def populate(self, req, ctx):
        error = None
        if req.method == 'POST':
            data = dict(req.get_fieldstorage())
            if data.get('new_password') != data.get('new_password_again'):
                error = 'New passwords do not match.'
            elif not data.get('new_password'):
                error = 'New password cannot be empty.'
            else:
                self.context.password = data['new_password']
                req.store.commit()
                req.throw_redirect(req.uri)

        ctx['user'] = self.context
        ctx['error'] = error

class Plugin(ViewPlugin, MediaPlugin):
    """
    The Plugin class for the user plugin.
    """

    forward_routes = (root_to_user,)
    reverse_routes = (user_url,)
    views = [(ApplicationRoot, 'users', UsersView),
             (User, '+index', UserEditView),
             (User, '+admin', UserAdminView),
             (User, '+changepassword', PasswordChangeView),
             (User, '+resetpassword', PasswordResetView),
             ]

    tabs = [
        ('users', 'Users', 'Display and edit all users',
         'users.png', 'users', 90, True)
    ]

    public_forward_routes = forward_routes
    public_reverse_routes = reverse_routes

    media = 'user-media'
