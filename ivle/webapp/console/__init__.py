from ivle.webapp.base.plugins import ViewPlugin
from ivle.webapp.console.service import ConsoleServiceRESTView

class Plugin(ViewPlugin):
    """
    The Plugin class for the console plugin.
    """
    urls = [
        ('console/service', ConsoleServiceRESTView),
    ]
