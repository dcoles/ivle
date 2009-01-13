# IVLE Configuration File
# conf/apps.py
# Configuration of plugin applications for IVLE
# These should not need to be modified by admins unless new applications are
# plugged in.

enable_debuginfo = False

# Allow App objects
# Notes:
# desc is a full description for the front page. It isn't required
# unless this app is in apps_on_home_page.
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
                    name = "Files",
                    desc = "Gives you access to all of your files and lets "
                           "you download, upload, edit and run them.",
                    icon = "browser.png",
                    useconsole = True,
                    requireauth = True,
                    hashelp = True)

app_fileservice = App(dir = "fileservice",
                    name = "File Service (AJAX server)",
                    requireauth = True,
                    hashelp = False)

app_console =     App(dir = "console",
                    name = "Console",
                    desc = "A Python console where you can try out code "
                           "without having to save and run it.",
                    icon = "console.png",
                    useconsole = False, # We use a full console in this app
                    requireauth = True,
                    hashelp = True)

app_consoleservice = App(dir = "consoleservice",
                    name = "Console Service",
                    requireauth = True,
                    hashelp = False)

app_tutorial =     App(dir = "tutorial",
                    name = "Worksheets",
                    desc = "Online tutorials and exercises for lab work.",
                    icon = "tutorial.png",
                    useconsole = True,
                    requireauth = True,
                    hashelp = True)

app_tutorialservice = App(dir = "tutorialservice",
                    name = "Tutorial Service",
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

app_help =      App(dir = "help",
                    name = "Help",
                    desc = "IVLE help pages",
                    icon = "help.png",
                    requireauth = True,
                    hashelp = False)

app_debuginfo = App(dir = "debuginfo",
                    name = "Debug Information",
                    requireauth = False,
                    hashelp = False)

app_forum = App(dir = "forum",
                    name = "Forum",
                    desc = "Discussion boards for material relating to "
                           "Informatics, IVLE and Python.",
                    icon = "forum.png",
                    requireauth = True,
                    hashelp = False)

app_tos = App(dir = "tos",
                    name = "Terms of Service",
                    requireauth = False,
                    hashelp = False)

app_settings = App(dir = "settings",
                    name = "Account Settings",
                    icon = "settings.png",
                    requireauth = True,
                    hashelp = True)

app_groups = App(dir = "groups",
                    name = "Group Management",
                    icon = "groups.png",
                    requireauth = True,
                    hashelp = True)

app_userservice = App(dir = "userservice",
                    name = "User Management Service",
                    requireauth = False,
                    hashelp = False)

app_diff = App(dir = "diff",
                    name = "Diff",
                    #icon = "forum.png",
                    requireauth = True,
                    hashelp = False)

app_svnlog = App(dir = "svnlog",
                    name = "Subversion Log",
                    requireauth = True,
                    hashelp = False)

app_subjects = App(dir = "subjects",
                    name = "Subjects",
                    desc = "Announcements and information about the subjects "
                           "you are enrolled in.",
                    icon = "subjects.png",
                    requireauth = False,
                    hashelp = False)

app_home = App(dir = "home",
                    name = "Home",
                    desc = "IVLE home page",
                    icon = "home.png",
                    requireauth = True,
                    hashelp = False)
                    
app_logout = App(dir = "logout",
                    name = "Logout",
                    requireauth = True,
                    hashelp = False)
# Mapping URL names to apps

app_url = {
    "files" : app_browser,
    "fileservice" : app_fileservice,
    "console" : app_console,
    "consoleservice" : app_consoleservice,
    "tutorial" : app_tutorial,
    "tutorialservice" : app_tutorialservice,
    "serve" : app_server,
    "download" : app_download,
    "help" : app_help,
    "forum" : app_forum,
    "tos" : app_tos,
    "settings" : app_settings,
    "groups" : app_groups,
    "userservice" : app_userservice,
    "diff" : app_diff,
    "svnlog" : app_svnlog,
    "subjects" : app_subjects,
    "home" : app_home,
    "logout" : app_logout,
}
if enable_debuginfo:
    app_url["debuginfo"] = app_debuginfo

# List of apps that go in the tabs at the top
# (The others are hidden unless they are linked to)
# Note: The values in this list are the URL names as seen in app_url.

apps_in_tabs = ["files", "tutorial", "console",
                "forum", "subjects", "help"]

# List of apps that go in the list on the home page
apps_on_home_page = ["subjects", "files", "tutorial", "console", "forum"]
