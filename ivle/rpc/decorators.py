'''Decorators useful for actions in the IVLE AJAX API.

The first argument to any method wrapped by these needs to be a request.
'''

from ivle.webapp.errors import MethodNotAllowed, Unauthorized

class require_method(object):
    '''Require that the request has been made with the specified HTTP method.
    '''
    def __init__(self, method):
        self.method = method

    def __call__(self, func):
        def method_or_die(req, *args, **kwargs):
           if req.method != self.method:
                raise MethodNotAllowed(allowed=[self.method])
           func(req, *args, **kwargs)
        return method_or_die

def require_admin(func):
    '''Require that the logged in user is an admin.'''
    def admin_or_die(req, *args, **kwargs):
       if not req.user or not req.user.admin:
            raise Unauthorized()
       func(req, *args, **kwargs)
    return admin_or_die
