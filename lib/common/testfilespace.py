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

# Module: TestFilespace
# Author: Dilshan Angampitiya
#         Steven Bird (revisions)
#         David Coles (revisions and moved to module)
# Date:   24/1/2008

import StringIO

class TestFilespace:
    """
    Our dummy file system which is accessed by code being tested.
    Implemented as a dictionary which maps filenames to strings
    """
    def __init__(self, files=None):
        "Initialise, optionally with filename-filedata pairs"

        if files == None:
            files = {}

        # dict mapping files to strings
        self._files = {}
        self._files.update(files)
        # set of file names
        self._modified_files = set([])
        # dict mapping files to stringIO objects
        self._open_files = {}

    def add_file(self, filename, data):
        " Add a file to the filespace "
        self._files[filename] = data

    def openfile(self, filename, mode='r'):
        """ Open a file from the filespace with the given mode.
        Return a StringIO subclass object with the file contents.
        """
        # currently very messy, needs to be cleaned up
        # Probably most of this should be in the initialiser to the TestStringIO
        
        import re

        if filename in self._open_files:
            raise IOError("File already open: %s" %filename)

        if not re.compile("[rwa][+b]{0,2}").match(mode):
            raise IOError("invalid mode %s" %mode)
        
        ## TODO: validate filename?
        
        mode.replace("b",'')
        
        # initialise the file properly (truncate/create if required)
        if mode[0] == 'w':
            self._files[filename] = ''
            self._modified_files.add(filename)
        elif filename not in self._files:
            if mode[0] == 'a':
                self._files[filename] = ''
                self._modified_files.add(filename)
            else:
                raise IOError(2, "Access to file denied: %s" %filename)

        # for append mode, remember the existing data
        if mode[0] == 'a':
            existing_data = self._files[filename]
        else:
            existing_data = ""

        # determine what operations are allowed
        reading_ok = (len(mode) == 2 or mode[0] == 'r')
        writing_ok = (len(mode) == 2 or mode[0] in 'wa')

        # for all writing modes, start off with blank file
        if mode[0] == 'w':
            initial_data = ''
        else:
            initial_data = self._files[filename]

        file_object = TestStringIO(initial_data, filename, self, reading_ok, writing_ok, existing_data)
        self._open_files[filename] = file_object
        
        return file_object

    def flush_all(self):
        """ Flush all open files
        """
        for file_object in self._open_files.values():
            file_object.flush()

    def updatefile(self,filename, data):
        """ Callback function used by an open file to inform when it has been updated.
        """
        if filename in self._open_files:
            self._files[filename] = data
            if self._open_files[filename].is_modified():
                self._modified_files.add(filename)
        else:
            raise IOError(2, "Access to file denied: %s" %filename)

    def closefile(self, filename):
        """ Callback function used by an open file to inform when it has been closed.
        """
        if filename in self._open_files:
            del self._open_files[filename]

    def get_modified_files(self):
        """" A subset of the filespace containing only those files which have been
        modified
        """
        modified_files = {}
        for filename in self._modified_files:
            modified_files[filename] = self._files[filename]

        return modified_files

    def get_open_files(self):
        " Return the names of all open files "
        return self._open_files.keys()
            
    def copy(self):
        """ Return a copy of the current filespace.
        Only the files are copied, not the modified or open file lists.
        """
        self.flush_all()
        return TestFilespace(self._files)

class TestStringIO(StringIO.StringIO):
    """
    A subclass of StringIO which acts as a file in our dummy file system
    """
    def __init__(self, string, filename, filespace, reading_ok, writing_ok, existing_data):
        """ Initialise with the filedata, file name and infomation on what ops are
        acceptable """
        StringIO.StringIO.__init__(self, string)
        self._filename = filename
        self._filespace = filespace
        self._reading_ok = reading_ok
        self._writing_ok = writing_ok
        self._existing_data = existing_data
        self._modified = False
        self._open = True

    # Override all standard file ops. Make sure that they are valid with the given
    # permissions and if so then call the corresponding method in StringIO
    
    def read(self, *args):
        if not self._reading_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.read(self, *args)

    def readline(self, *args):
        if not self._reading_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.readline(self, *args)

    def readlines(self, *args):
        if not self._reading_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.readlines(self, *args)

    def seek(self, *args):
        if not self._reading_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.seek(self, *args)

    def truncate(self, *args):
        self._modified = True
        if not self._writing_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.truncate(self, *args)
        
    def write(self, *args):
        self._modified = True
        if not self._writing_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.write(self, *args)

    def writelines(self, *args):
        self._modified = True
        if not self._writing_ok:
            raise IOError(9, "Bad file descriptor")
        else:
            return StringIO.StringIO.writelines(self, *args)

    def is_modified(self):
        " Return true if the file has been written to, or truncated"
        return self._modified
        
    def flush(self):
        " Update the contents of the filespace with the new data "
        self._filespace.updatefile(self._filename, self._existing_data+self.getvalue())
        return StringIO.StringIO.flush(self)

    def close(self):
        " Flush the file and close it "
        self.flush()
        self._filespace.closefile(self._filename)
        return StringIO.StringIO.close(self)

