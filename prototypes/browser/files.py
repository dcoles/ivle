# files.py - Publisher mod_python program
#
# Performs directory operations and returns result data in JSON format
# Designed to be used with an AJAX front end.
# PROOF-OF-CONCEPT ONLY
#
# Author: Matt Giuca

# Note: All operations unless noted return a directory listing in JSON format.

from mod_python import apache
import os
import time
# JSON encoder
import encoder

content_type = "text/html"
# application/json is the "best" content type but is not good for debugging
# because Firefox just tries to download it
#content_type = "application/json"
enc = encoder.JSONEncoder()

getfile_content_type="text/html"
#getfile_content_type="application/octet-stream"

root = "/home/mgiuca/playground/"

greqprint = None
def set_greqprint(req):
    """Sets greqprint to a function which prints to the given req."""
    global greqprint
    def p(str):
        req.write(str + '\n')
    greqprint = p

def safe_path_to_local(path):
    """This function takes a path which is relative to the browser root
    (global "root"). It normalises it and returns an absolute path on the
    system. It checks to make sure the path is a SUBDIRECTORY of root,
    and does not allow paths to go to a parent or sibling of root.
    
    Returns None if the path was invalid.
    """
    global root
    # First normalise the path
    path = os.path.normpath(path)
    # Now if it begins with ".." then it's illegal
    if path.startswith(".."):
        return None
    # Now join it onto the root
    path = os.path.join(root, path)
    # Just to be safe, normalise it again and make sure it is a subdirectory
    # of root.
    # Normcase only does anything on Windows
    path = os.path.normcase(os.path.normpath(path))
    if not path.startswith(os.path.normcase(os.path.normpath(root))):
        return None
    return path

def init(req, path):
    """Performs setup common to all actions (NOT a user-callable action).
    Returns a new path which is safe (guaranteed within the root), and is an
    absolute path."""
    set_greqprint(req)
    req.content_type = content_type
    # filenames :: [string]
    path = safe_path_to_local(path)
    if path == None:
        return "null"
    return path

def dirlisting(path):
    """Get a directory listing from a path. The path is a safe, absolute path.
    Returns a dictionary of file listing info. NOT to be called directly."""
    filenames = os.listdir(path)
    filenames.sort()
    return map(file_to_fileinfo(path), filenames)

def ls(req, path="."):
    """Gets a directory listing of a given path on the server, in JSON
    format."""
    path = init(req, path)
    try:
        files = dirlisting(path)
    except OSError, (errno, errmsg):
        return enc.encode({"error": errmsg})
    req.write(enc.encode(files))
    return ""

def rm(req, path, filename):
    """Removes a file, and returns a directory listing of the path."""
    # dirpath is the directory without the file attached
    dirpath = init(req, path)
    # filepath is the path to the file being deleted
    filepath = safe_path_to_local(os.path.join(path, filename))
    if filepath == None:
        return "null"
    try:
        os.remove(filepath)
        files = dirlisting(dirpath)
    except OSError, (errno, errmsg):
        return enc.encode({"error": errmsg})
    req.write(enc.encode(files))
    return ""

def rename(req, path, fromfilename, tofilename):
    """Renames a file, and returns a directory listing of the path."""
    # dirpath is the directory without the file attached
    dirpath = init(req, path)
    # filepath is the path to the file being deleted
    fromfilepath = safe_path_to_local(os.path.join(path, fromfilename))
    tofilepath = safe_path_to_local(os.path.join(path, tofilename))
    if fromfilepath == None or tofilepath == None:
        return "null"
    try:
        os.rename(fromfilepath, tofilepath)
        files = dirlisting(dirpath)
    except OSError, (errno, errmsg):
        return enc.encode({"error": errmsg})
    req.write(enc.encode(files))
    return ""

def file_to_fileinfo(path):
    """Given a filename (relative to a given path), gets all the info "ls"
    needs to display about the filename. Returns a dict mapping a number of
    fields which are returned."""
    # Note: curried so it can be used with map
    def ftf(filename):
        fullpath = os.path.join(path, filename)
        d = {"filename" : filename}
        d["isdir"] = os.path.isdir(fullpath)
        stat = os.stat(fullpath)
        d["size"] = stat.st_size
        d["mtime"] = time.ctime(stat.st_mtime)
        return d
    return ftf

def getfile(req, path, filename):
    """Returns the contents of a given file."""
    filepath = init(req, os.path.join(path, filename))
    req.content_type = getfile_content_type
    # open the file and copy its contents into req
    try:
        file = open(filepath, "r")
    except IOError, (errno, errmsg):
        return enc.encode({"error": errmsg})

    # TODO: Binary instead of per-line
    for line in file:
        req.write(line)
    file.close()
    return ""

def putfile(req, path, filename, data):
    """Writes data to a file, overwriting it if it exists and creating it if
    it doesn't. The data should be postdata but this is a proof-of-concept.
    Returns a directory listing, as the other commands do.
    """
    # dirpath is the directory without the file attached
    dirpath = init(req, path)
    # filepath is the path to the file being deleted
    filepath = safe_path_to_local(os.path.join(path, filename))
    if filepath == None:
        return "null"
    # open the file and copy its contents into req
    try:
        file = open(filepath, "w")
    except IOError, (errno, errmsg):
        return enc.encode({"error": errmsg})

    file.write(data)
    file.close()

    try:
        files = dirlisting(dirpath)
    except OSError, (errno, errmsg):
        return enc.encode({"error": errmsg})
    req.write(enc.encode(files))
    return ""

