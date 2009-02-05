from ivle.webapp.base.plugins import BasePlugin
from ivle.webapp.console.service import ConsoleServiceRESTView

class Plugin(BasePlugin):
    """
    The Plugin class for the console plugin.
    """
    urls = [
        ('console/service', ConsoleServiceRESTView)
    ]
