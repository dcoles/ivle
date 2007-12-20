# IVLE Configuration File
# conf/mimetypes.py
# Configuration of mime types
# These should not need to be modified by admins unless there are problems
# with file type identification.

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

