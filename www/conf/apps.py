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
    def __repr__(self):
        return ("App(dir=" + repr(self.dir) + ", name=" + repr(self.name) +
            ", requireauth=" + repr(self.requireauth) + ", hashelp="
            + repr(self.hashelp) + ")")

# Application definitions

app_browser =   App(dir = "browser",
                    name = "File Browser",
                    requireauth = True,
                    hashelp = True)

app_editor =   App(dir = "editor",
                    name = "Text Editor",
                    requireauth = True,
                    hashelp = True)

app_fileservice = App(dir = "fileservice",
                    name = "File Service (AJAX server)",
                    requireauth = True,
                    hashelp = False)

app_console =     App(dir = "console",
                    name = "Console",
                    requireauth = True,
                    hashelp = True)

app_tutorial =     App(dir = "tutorial",
                    name = "Tutorial",
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
