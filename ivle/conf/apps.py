# IVLE Configuration File
# conf/apps.py
# Configuration of plugin applications for IVLE
# These should not need to be modified by admins unless new applications are
# plugged in.

# Allow App objects
# Notes:
# icon is a string of a file basename. The icon files are found in
# app_icon_dir, defined below.
class App:
    def __init__(self, dir, name, desc=None, icon = None,
        useconsole = False, requireauth = True, hashelp = False):
        self.dir = dir
        self.name = name
        self.desc = desc
        self.icon = icon
        self.useconsole = useconsole
        self.requireauth = requireauth
        self.hashelp = hashelp
    def __repr__(self):
        return ("App(dir=%s, name=%s, desc=%s, icon=%s, requireauth=%s, "
                "hashelp=%s)" % (repr(self.dir), repr(self.name),
                repr(self.desc), repr(self.icon), repr(self.requireauth),
                repr(self.hashelp)))

# Which application to use for "public host" URLs.
# (See conf.py)
public_app = "serve"

# Application definitions

app_fileservice = App(dir = "fileservice",
                    name = "File Service (AJAX server)",
                    requireauth = True,
                    hashelp = False)

app_server =    App(dir = "server",
                    name = "Server",
                    requireauth = True,
                    hashelp = False)

app_download =  App(dir = "download",
                    name = "Download",
                    requireauth = True,
                    hashelp = False)
app_userservice = App(dir = "userservice",
                    name = "User Management Service",
                    requireauth = False,
                    hashelp = False)

# Mapping URL names to apps

app_url = {
    "fileservice" : app_fileservice,
    "serve" : app_server,
    "download" : app_download,
    "userservice" : app_userservice,
}
