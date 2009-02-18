import datetime

from ivle.database import User
from ivle.dispatch.request import Request

class FakeUser(User):
    login = u'fakeuser'
    state = u'enabled'
    rolenm = u'student'
    unixid = 5000
    nick = u'Fake User'
    pass_exp = None
    acct_exp = None
    last_login = datetime.datetime.now()
    svn_pass = u'somepass'
    email = u'fakeuser@example.com'
    fullname = u'Fake Fixture User'
    studentid = u'1234'

class FakeRequest(Request):
    '''A fake request object, for use as a fixture in tests.

    This tries to behave fairly closely to an ivle.dispatch.request.Request,
    but without needing a web server.
    '''
    def __init__(self):
        '''Set sane defaults.'''

        # Some fields are omitted because they make no sense in the new model.
        self.headers_written = False
        self.publicmode = False
        self.method = 'GET'
        self.uri = '/'
        self.user = FakeUser()
        self.hostname = 'fakehost'
        self.headers_in = {}
        self.headers_out = {}

        # We don't want DB access in tests (by default)
        self.store = None

        # Default values for the output members
        self.status = Request.HTTP_OK
        self.content_type = None        # Use Apache's default
        self.location = None
        self.title = None     # Will be set by dispatch before passing to app
        self.styles = []
        self.scripts = []
        self.scripts_init = []
        self.request_body = ''
        self.response_body = ''
        # In some cases we don't want the template JS (such as the username
        # and public FQDN) in the output HTML. In that case, set this to 0.
        self.write_javascript_settings = True
        self.got_common_vars = False

    def __del__(self):
        '''Cleanup, but don't close the nonexistent store.'''
        if self.store is not None:
            self.store.close()

    def ensure_headers_written(self):
        '''Fake a write of the HTTP and HTML headers if they haven't already
           been written.'''
        pass

    def read(self, len=None):
        if len is None:
            data = self.request_body
            self.request_body = ''
        else:
            data = self.request_body[:len]
            self.request_body = self.request_body[len:]
        return data

    def write(self, string, flush=1):
        '''Write a string to the internal output storage.'''
        self.ensure_headers_written()
        if isinstance(string, unicode):
            self.response_body += string.encode('utf8')
        else:
            self.response_body += string

    def flush(self):
        '''Fake a flush.'''
        pass

