import os, inspect

import genshi
import genshi.template

import ivle.conf
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.errors import NotFound, Forbidden

def generate_toc(plugins, req):
    toc = {}
    for plugin in plugins:
        if hasattr(plugin, 'help'):
            # Get the dir the plugin resides in
            plugindir = os.path.dirname(inspect.getmodule(plugin).__file__)
            add_dict(toc, plugin.help, plugindir)
    return toc

def add_dict(newdict, curdict, plugin):
    for key in curdict:
        if key not in newdict:
            newdict[key] = {}
        if isinstance(curdict[key], dict):
            add_dict(newdict[key], curdict[key], plugin)
        else:
            newdict[key] = os.path.join(plugin, curdict[key])
    return newdict

class HelpView(XHTMLView):
    """Shows the help file for the specified path."""

    template = 'helpview.html'

    def __init__(self, req, path):
        self.paths = path.split('/')

    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['help.css']

        helpfile = generate_toc(req.plugin_index[ViewPlugin], req)
        try:
            for path in self.paths:
                if len(path) > 0:
                    helpfile = helpfile[path]
        except (KeyError, TypeError):
            # Traversal failed. We 404.
            raise NotFound()

        if not isinstance(helpfile, basestring):
            # It's a virtual directory.
            raise Forbidden()

        ctx['helpfile'] = helpfile


class HelpToCView(XHTMLView):
    """Displays the help Table of Contents."""
    appname = 'help'
    template = 'toc.html'

    def populate(self, req, ctx):
        ctx['toc'] = generate_toc(req.plugin_index[ViewPlugin], req)


class Plugin(ViewPlugin, MediaPlugin):
    """The plugin for viewing help files."""

    urls = [
        ('+help', HelpToCView),
        ('+help/*path', HelpView)
    ]

    tabs = [
        ('help', 'Help', 'IVLE help pages', 'help.png', '+help', 100)
    ]

    media = 'media'
