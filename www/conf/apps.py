# IVLE Configuration File
# conf/apps.py
# Configuration of plugin applications for IVLE
# These should not need to be modified by admins unless new applications are
# plugged in.

# Allow App objects
# Note: icon is a string of a file basename. The icon files are found in
# app_icon_dir, defined below.
class App:
    def __init__(self, dir, name, icon = None, requireauth = True,
        hashelp = False):
        self.dir = dir
        self.name = name
        self.icon = icon
        self.requireauth = requireauth
        self.hashelp = hashelp
    def __repr__(self):
        return ("App(dir=" + repr(self.dir) + ", name=" + repr(self.name) +
            ", icon=" + repr(self.icon) +
            ", requireauth=" + repr(self.requireauth) + ", hashelp="
            + repr(self.hashelp) + ")")

# Directory where app icons are stored, relative to the IVLE root.
app_icon_dir = "media/images/apps"
# Small version of icons (16x16, for favicon)
app_icon_dir_small = "media/images/apps/small"

# Which application to load by default (if the user navigates to the top level
# of the site). This is the app's URL name.
# Note that if this app requires authentication, the user will first be
# presented with the login screen.
default_app = "files"
# Which application to use for "public host" URLs.
# (See conf.py)
public_app = "serve"

# Application definitions

app_browser =   App(dir = "browser",
                    name = "File Browser",
                    icon = "browser.png",
                    requireauth = True,
                    hashelp = True)

app_editor =   App(dir = "editor",
                    name = "Text Editor",
                    icon = "editor.png",
                    requireauth = True,
                    hashelp = True)

app_fileservice = App(dir = "fileservice",
                    name = "File Service (AJAX server)",
                    requireauth = True,
                    hashelp = False)

app_console =     App(dir = "console",
                    name = "Console",
                    icon = "console.png",
                    requireauth = True,
                    hashelp = True)

app_consoleservice = App(dir = "consoleservice",
                    name = "Console Service",
                    requireauth = True,
                    hashelp = False)

app_tutorial =     App(dir = "tutorial",
                    name = "Tutorial",
                    icon = "tutorial.png",
                    requireauth = True,
                    hashelp = True)

app_server =    App(dir = "server",
                    name = "Server",
                    requireauth = False,
                    hashelp = False)

app_download =  App(dir = "download",
                    name = "Download",
                    requireauth = True,
                    hashelp = False)

app_help =      App(dir = "help",
                    name = "Help",
                    icon = "help.png",
                    requireauth = True,
                    hashelp = False)

app_debuginfo = App(dir = "debuginfo",
                    name = "Debug Information",
                    requireauth = False,
                    hashelp = False)

# Mapping URL names to apps

app_url = {
    "files" : app_browser,
    "edit" : app_editor,
    "fileservice" : app_fileservice,
    "console" : app_console,
    "consoleservice" : app_consoleservice,
    "tutorial" : app_tutorial,
    "serve" : app_server,
    "download" : app_download,
    "help" : app_help,
    #"debuginfo" : app_debuginfo,
}

# List of apps that go in the tabs at the top
# (The others are hidden unless they are linked to)
# Note: The values in this list are the URL names as seen in app_url.

apps_in_tabs = ["files", "edit", "console", "tutorial", "help"]
