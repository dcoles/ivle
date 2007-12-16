# IVLE Configuration File
# conf/apps.py
# Configuration of plugin applications for IVLE
# These should not need to be modified by admins unless new applications are
# plugged in.

# Allow App objects
class App:
    def __init__(self, dir, name, requireauth = True, hashelp = False):
        self.dir = dir
        self.name = name
        self.requireauth = requireauth
        self.hashelp = hashelp

# Application definitions

app_dummy =     App(dir = "dummy",
                    name = "My Dummy App",
                    requireauth = True,
                    hashelp = True)

app_server =    App(dir = "server",
                    name = "Server",
                    requireauth = False,
                    hashelp = False)

app_help =      App(dir = "help",
                    name = "Help",
                    requireauth = True,
                    hashelp = False)

# Mapping URL names to apps

app_url = {
    "dummy" : app_dummy,
    "serve" : app_server,
    "help" : app_help,
}

# List of apps that go in the tabs at the top
# (The others are hidden unless they are linked to)
# Note: The values in this list are the URL names as seen in app_url.

apps_in_tabs = ["dummy", "help"]
