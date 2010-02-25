class ApplicationRoot(object):
    """Root of the IVLE path namespace."""
    def __init__(self, req):
        # store and user are properties so we don't construct a store
        # unless something actually retrieves the store or user.
        self.req = req

    @property
    def config(self):
        return self.req.config

    @property
    def store(self):
        return self.req.store

    @property
    def user(self):
        return self.req.user
