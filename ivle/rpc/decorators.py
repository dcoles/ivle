'''Decorators useful for actions in the IVLE AJAX API.

The first argument to any method wrapped by these needs to be a request.
'''

class require_method(object):
    '''Require that the request has been made with the specified HTTP method.
    '''
    def __init__(self, method):
        self.method = method

    def __call__(self, func):
        def method_or_die(req, *args, **kwargs):
           if req.method != self.method:
               req.throw_error(req.HTTP_METHOD_NOT_ALLOWED,
               "Only %s requests can be made to this action." % self.method)
           func(req, *args, **kwargs)
        return method_or_die

class require_cap(object):
    '''Require that the logged in user has the specified capability.'''
    def __init__(self, cap):
        self.cap = cap

    def __call__(self, func):
        def cap_or_die(req, *args, **kwargs):
           if not req.user or not req.user.hasCap(self.cap):
               req.throw_error(req.HTTP_FORBIDDEN,
               "You do not have permission to use this action.")
           func(req, *args, **kwargs)
        return cap_or_die
