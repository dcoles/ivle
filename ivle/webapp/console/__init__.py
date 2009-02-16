from ivle.webapp.base.plugins import ViewPlugin, OverlayPlugin, MediaPlugin
from ivle.webapp.console.service import ConsoleServiceRESTView
from ivle.webapp.console.overlay import ConsoleOverlay
from ivle.webapp.base.xhtml import XHTMLView


class ConsoleView(XHTMLView):
    appname = 'console'
    help = 'Console'

    plugin_scripts = {'ivle.webapp.console': ['console.js']}
    plugin_styles  = {'ivle.webapp.console': ['console.css']}
    plugin_scripts_init = ['console_init']

    # Don't load the console overlay when we already have a console.
    overlay_blacklist = [ConsoleOverlay]

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        ctx['windowpane'] = False
        ctx['start_body_attrs'] = {}

class Plugin(ViewPlugin, OverlayPlugin, MediaPlugin):
    urls = [
        ('console/service', ConsoleServiceRESTView),
        ('console', ConsoleView),
    ]
    tabs = [
        ('console', 'Console', 'A Python console where you can try out code '
         'without having to save and run it.', 'console.png', 'console', 3)
    ]
    overlays = [
        ConsoleOverlay,
    ]
    media = 'media'
    help = {'Console': 'help.html'}
