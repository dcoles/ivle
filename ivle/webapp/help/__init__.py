import os, inspect

import genshi
import genshi.template

from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.errors import NotFound, Forbidden
from ivle.webapp.publisher.decorators import forward_route, reverse_route
from ivle.webapp.publisher import ROOT
from ivle.webapp import ApplicationRoot

def generate_toc(plugins):
    """Create a root HelpTree with content from the plugins."""
    toc = HelpTree(None, 'Help', {})
    for plugin in plugins:
        if hasattr(plugin, 'help'):
            # Get the dir the plugin resides in
            plugindir = os.path.dirname(inspect.getmodule(plugin).__file__)
            add_dict(toc, plugin.help, plugindir)
    return toc

def add_dict(newdict, curdict, plugin):
    """Deeply merge curdict into newdict."""
    for key in curdict:
        if isinstance(curdict[key], dict):
            if key not in newdict:
                newdict[key] = HelpTree(newdict, key, {})
            add_dict(newdict[key], curdict[key], plugin)
        else:
            newdict[key] = HelpEntry(newdict, key, os.path.join(plugin, curdict[key]))
    return newdict

class HelpTreeView(XHTMLView):
    tab = 'help'
    template = 'toc.html'
    
    """Shows the help file for the specified path."""
    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['help.css']

        ctx['req'] = req
        ctx['context'] = self.context
        ctx['HelpTree'] = HelpTree
        ctx['HelpEntry'] = HelpEntry

class HelpEntryView(XHTMLView):
    tab = 'help'
    template = 'helpview.html'
    
    """Shows the help file for the specified path."""
    def authorize(self, req):
        return req.user is not None

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['help.css']
        
        ctx['helpfile'] = self.context.file

class HelpTree(dict):
    def __init__(self, parent, name, tree):
        super(HelpTree, self).__init__(tree)
        self.parent = parent
        self.name = name

class HelpEntry(object):
    def __init__(self, parent, name, file):
        self.parent = parent
        self.name = name
        self.file = file

@forward_route(ApplicationRoot, '+help')
def root_to_helptree(root):
    return generate_toc(root.config.plugin_index[ViewPlugin])

@forward_route(HelpTree, argc=1)
def helptree_to_help(help, subhelp_name):
    try:
        return help[subhelp_name]
    except KeyError:
        # No help entry of that name
        return None

@reverse_route(HelpTree)
def helptree_url(helptree):
    if helptree.parent is None:
        return (ROOT, '+help')
    return (helptree.parent, helptree.name)

@reverse_route(HelpEntry)
def helpentry_url(helpentry):
    return (helpentry.parent, helpentry.name)

class Plugin(ViewPlugin, MediaPlugin):
    """The plugin for viewing help files."""
    forward_routes = (root_to_helptree, helptree_to_help)
    reverse_routes = (helptree_url, helpentry_url)

    views = [(HelpTree, '+index', HelpTreeView),
             (HelpEntry, '+index', HelpEntryView)]

    tabs = [
        ('help', 'Help', 'Get help with IVLE', 'help.png', '+help', 100)
    ]

    media = 'media'
