# IVLE Configuration File
# conf/server.py
# Configuration for Server ('serve') app.
# These should not need to be modified by admins unless new languages become
# supported.

# Note that this configuration file uses mime types to identify files.
# conf/mimetypes.py may need to be modified to configure mime types outside of
# the system's default mime types.

# Mapping mime types to interpreters
# Interpreters are built-in to IVLE, and identified by their string names.
# Available interpreters are:
#   cgi-generic
#       Runs any executable file as a CGI program
#   cgi-python
#       Runs a Python script as a CGI program
#   python-server-page
#       Runs a Python Server Page (psp) file

interpreters = {
    "text/x-python" : "cgi-python",
    "text/x-python-server-page" : "python-server-page",
}

# Non-interpreted files fall back to either being served directly, or
# returning a 403 Forbidden.
# This decision can either be made with a blacklist or a whitelist.

blacklist_served_filetypes = False

# blacklist_served_filetypes = False causes IVLE to disallow all filetypes by
# default, and use served_filetypes_whitelist for exceptions.
# blacklist_served_filetypes = True causes IVLE to allow all filetypes by
# default, and use served_filetypes_blacklist for exceptions.

# The whitelist/blacklist dictionaries are sets of mime types to allow or
# disallow respectively.

served_filetypes_whitelist = set([
    "application/ecmascript",
    "application/octet-stream",
    "application/pdf",
    "application/postscript",
    "application/javascript",
    "application/json",
    "application/xhtml+xml",
    "application/xml",
    "application/zip",

    "audio/x-wav",
    "audio/mpeg",
    "audio/midi",

    "image/gif",
    "image/jpeg",
    "image/png",

    "text/css",
    "text/csv",
    "text/csv",
    "text/html",
    "text/plain",
    "text/xml",
])

served_filetypes_blacklist = set([
    "application/x-executable",
])

