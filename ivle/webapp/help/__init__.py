import os, inspect

import genshi
import genshi.template

import ivle.conf
from ivle.webapp.base.plugins import ViewPlugin
from ivle.webapp.base.xhtml import XHTMLView

def help_url(plugin, path):
    '''Generates a URL to a media file.
    
    Plugin must be a string, which is put into the path literally.'''

    return os.path.join(ivle.conf.root_dir, plugin, path)

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
            newdict[key] = help_url(plugin, curdict[key])
    return newdict

class HelpView(XHTMLView):
    """Shows the help file for the specified path."""
    
    template = 'helpview.html'
    
    def __init__(self, req, path):
        self.paths = path.split('/')
    
    def populate(self, req, ctx):
        helpfile = generate_toc(req.plugin_index[ViewPlugin], req)
        try:
            for path in self.paths:
                helpfile = helpfile[path]
                ctx['helpfile'] = helpfile
        except KeyError:
            pass
            

class HelpToc(XHTMLView):
    """Displays the help Table of Contents."""
    appname = 'help'
    template = 'toc.html'
    
    def populate(self, req, ctx):
        ctx['toc'] = generate_toc(req.plugin_index[ViewPlugin], req)
        
        

class Plugin(ViewPlugin):
    """The plugin for viewing help files."""
    
    urls = [
        ('+help', HelpToc),
        ('+help/*path', HelpView)
    ]
