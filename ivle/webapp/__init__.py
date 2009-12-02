class ApplicationRoot(object):
    """Root of the IVLE path namespace."""
    def __init__(self, config, store, user):
        self.config = config
        self.store = store
        self.user = user
