from ivle.webapp.base.plugins import ViewPlugin, OverlayPlugin, MediaPlugin
from ivle.webapp.console.service import ConsoleServiceRESTView
from ivle.webapp.console.overlay import ConsoleOverlay
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp import ApplicationRoot


class ConsoleView(XHTMLView):
    tab = 'console'
    help = 'Console'
    breadcrumb_text = 'Console'

    # Overide the the standard constructor view
    def __init__(self, *args, **kwargs):
        super(ConsoleView, self).__init__(*args, **kwargs)

        self.plugin_scripts = {'ivle.webapp.console': ['console.js']}
        self.plugin_styles  = {'ivle.webapp.console': ['console.css']}
        self.plugin_scripts_init = ['console_init']

        # Don't load the console overlay when we already have a console.
        self.overlay_blacklist = [ConsoleOverlay]

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        ctx['windowpane'] = False
        ctx['start_body_attrs'] = {'class': 'console_body'}

class Plugin(ViewPlugin, OverlayPlugin, MediaPlugin):
    views = [(ApplicationRoot, ('console', '+index'), ConsoleView),
             (ApplicationRoot, ('console', 'service'), ConsoleServiceRESTView),
             ]

    tabs = [
        ('console', 'Console', 'Try out your code in a Python console',
         'console.png', 'console', 3)
    ]

    overlays = [
        ConsoleOverlay,
    ]

    media = 'media'
    help = {'Console': 'help.html'}
