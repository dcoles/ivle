from ivle.webapp.base.plugins import ViewPlugin, OverlayPlugin, MediaPlugin
from ivle.webapp.console.service import ConsoleServiceRESTView
from ivle.webapp.console.overlay import ConsoleOverlay
from ivle.webapp.base.xhtml import XHTMLView


class ConsoleView(XHTMLView):
    appname = 'console'

    plugin_scripts = {'ivle.webapp.console': ['console.js']}
    plugin_styles  = {'ivle.webapp.console': ['console.css']}
    plugin_scripts_init = ['console_init']

    # Don't load the console overlay when we already have a console.
    overlay_blacklist = [ConsoleOverlay]

    def populate(self, req, ctx):
        ctx['windowpane'] = False


class Plugin(ViewPlugin, OverlayPlugin, MediaPlugin):
    """
    The Plugin class for the console plugin.
    """
    urls = [
        ('console/service', ConsoleServiceRESTView),
        ('console', ConsoleView),
    ]
    overlays = [
        ConsoleOverlay,
    ]
    media = 'media'
