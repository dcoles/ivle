from ivle.webapp.base.plugins import ViewPlugin
from ivle.webapp.base.plugins import OverlayPlugin
from ivle.webapp.console.service import ConsoleServiceRESTView
from ivle.webapp.console.overlay import ConsoleOverlay

class Plugin(ViewPlugin, OverlayPlugin):
    """
    The Plugin class for the console plugin.
    """
    urls = [
        ('console/service', ConsoleServiceRESTView),
    ]
    overlays = [
        ConsoleOverlay,
    ]
    media = 'media'
