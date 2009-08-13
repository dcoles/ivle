import os, inspect

import genshi
import genshi.template

from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.errors import NotFound, Forbidden
from ivle.webapp.publisher.decorators import forward_route, reverse_route
from ivle.webapp import ApplicationRoot

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

class HelpTreeView(XHTMLView):
    tab = 'help'
    template = 'toc.html'
    
    """Shows the help file for the specified path."""
    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['help.css']

        ctx['toc'] = self.context.tree

class HelpEntryView(XHTMLView):
    tab = 'help'
    template = 'helpview.html'
    
    """Shows the help file for the specified path."""
    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['help.css']

        ctx['helpfile'] = self.context.file

class HelpTree(object):
    def __init__(self, tree):
        self.tree = tree

class HelpEntry(object):
    def __init__(self, file):
        self.file = file

@forward_route(ApplicationRoot, '+help')
def root_to_helptree(root):
    return HelpTree(generate_toc(root.config.plugin_index[ViewPlugin], None))

@forward_route(HelpTree, argc=1)
def helptree_to_help(help, subhelp_name):
    try:
        sub = help.tree[subhelp_name]
        if type(sub) is dict:
            return HelpTree(sub)
        else:
            return HelpEntry(sub)
    except KeyError:
        # No help entry of that name
        return None

class Plugin(ViewPlugin, MediaPlugin):
    """The plugin for viewing help files."""
    forward_routes = (root_to_helptree, helptree_to_help)
    views = [(HelpTree, '+index', HelpTreeView),
             (HelpEntry, '+index', HelpEntryView)]

    tabs = [
        ('help', 'Help', 'Get help with IVLE', 'help.png', '+help', 100)
    ]

    media = 'media'
