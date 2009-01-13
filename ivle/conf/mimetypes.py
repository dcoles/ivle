# IVLE Configuration File
# conf/mimetypes.py
# Configuration of mime types
# These should not need to be modified by admins unless there are problems
# with file type identification.

# These settings, in conjunction with Python's mimetypes library,
# are used in various apps, including server and fileservice
# (and by extension, browser and editor), to determine the mime type of
# a given file.

# All files served whose mime type cannot be guessed will be served as this
# type.
default_mimetype = "text/plain"

# Mapping file extensions to mime types
# Note that IVLE uses Python's mimetype library which looks in a bunch of
# files such as /etc/mime.types. This section allows you to add new mime types
# solely for use in IVLE.
# File extensions should include the leading '.'.

additional_mime_types = {
    ".py" : "text/x-python",    # Redundant, but just in case
    ".psp" : "text/x-python-server-page",
    ".js" : "application/javascript",   # Override bad default
}

# Mapping mime types to friendly names

nice_mimetypes = {
    "text/x-python" : "Python source code",
    "text/plain" : "Text file",
    "text/html" : "HTML file",
    "image/png" : "PNG image",
}

