# IVLE Configuration File
# conf/apps.py
# Configuration of plugin applications for IVLE
# These should not need to be modified by admins unless new applications are
# plugged in.

# Allow App objects
class App:
    pass

# Application definitions

app_dummy = App()
app_dummy.dir = "dummy"
app_dummy.name = "My Dummy App"
app_dummy.requireauth = True
app_dummy.hashelp = True

app_help = App()
app_help.dir = "help"
app_help.name = "Help"
app_help.requireauth = True
app_help.hashelp = False

# Mapping URL names to apps

app_url = {
    "dummy" : app_dummy,
    "help" : app_help,
}

# List of apps that go in the tabs at the top
# (The others are hidden unless they are linked to)
# Note: The values in this list are the URL names as seen in app_url.

apps_in_tabs = ["dummy", "help"]
