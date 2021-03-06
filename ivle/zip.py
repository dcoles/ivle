# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2008 The University of Melbourne
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# Module: zip
# Author: Matt Giuca
# Date: 17/1/2008

# ZIP function wrappers. Provides easy methods for reading and writing zip
# files for the purpose of the IVLE file browser.

import os
import os.path
import zipfile

from ivle import studpath

def make_zip(basepath, paths, file):
    """Zips up a bunch of files on the student file space and writes it as
    a zip file.

    basepath: Path relative to student home. All file paths will be made
    relative to this path, such that unzipping the file in this path will
    place the files back in their original places.
    paths: List of paths relative to basepath. These are the files to be
    zipped. All paths must be relative.
    file: Either a filename to write to, or a file-like object.

    Throws an OSError if one or more of the files cannot be read. This error
    will be thrown before any writing takes place.
    """
    # First make sure all the files are valid
    newpaths = []       # Store tuples of (path, localpath)
    for path in paths:
        if len(path) == 0 or path[0] == os.sep:
            raise OSError("ZIP: Invalid path")
        else:
            # Relative to req.path
            relpath = os.path.join(basepath, path)

        #_, r = studpath.url_to_local(relpath)
        r = relpath
        if r is None:
            raise OSError("ZIP: Invalid path")
        if not os.access(r, os.R_OK):
            raise OSError("ZIP: Could not access a file")
        newpaths.append((path, r))

    # Now open the zip file and write each path to it
    zip = zipfile.ZipFile(file, 'w')

    for (path, localpath) in newpaths:
        if os.path.isdir(localpath):
            # Walk the directory tree
            if len(localpath) > 0 and localpath[-1] != os.sep:
                localpath += os.sep
            def error(err):
                raise OSError("ZIP: Could not access a file")
            for (dirpath, dirnames, filenames) in \
                os.walk(localpath, onerror=error):
                # Do not traverse into .svn directories
                try:
                    dirnames.remove(".svn")
                except ValueError:
                    pass
                # dirpath is local. Make arc_dirpath, relative to root
                arc_dirpath = os.path.join(path, dirpath[len(localpath):])
                for filename in filenames:
                    zip.write(os.path.join(dirpath, filename),
                                os.path.join(arc_dirpath, filename))
        else:
            zip.write(localpath, path)

    zip.close()

def unzip(path, file, overwrite=False):
    """Unzips a zip file (or file-like object) into a path.
    Note: All files go directly into the path. To avoid having a "zip bomb"
    situation, the zip file should have a single directory in it with all the
    files.
    The path is an absolute path in the current filesystem
    (if this code is executed inside the jail, then it's inside the jail).
    """
    # XXX: Really bad, but circular imports need avoiding.
    from ivle.fileservice_lib.exceptions import WillNotOverwrite

    zip = zipfile.ZipFile(file, 'r')
    # First test the zip file
    if zip.testzip() is not None:
        raise OSError("ZIP: Bad zip file")

    if (not overwrite):
        for filename in zip.namelist():
            localpath = os.path.join(path, filename)
            if os.path.exists(localpath):
                raise WillNotOverwrite(filename)

    for filename in zip.namelist():
        localpath = os.path.join(path, filename)
        # Create directory for filename
        (file_dir, _) = os.path.split(localpath)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        
        if filename.endswith(os.sep):
            # Is a directory make the directory
            if not os.path.exists(localpath):
                os.mkdir(localpath)
        else:
            filedata = zip.read(filename)
            f = open(localpath, 'w')
            f.write(filedata)
            f.close()
