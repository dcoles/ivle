# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2008 The University of Melbourne
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

# Module: Subversion utilities
# Author: William Grant
# Date:   16/07/2008

import stat

import pysvn

def revision_from_string(r_str):
    if r_str is None:
        pass
    elif r_str == "HEAD":
        return pysvn.Revision( pysvn.opt_revision_kind.head )
    elif r_str == "WORKING":
        return pysvn.Revision( pysvn.opt_revision_kind.working )
    elif r_str == "BASE":
        return pysvn.Revision( pysvn.opt_revision_kind.base )
    else:
        # Is it a number?
        try:
            r = int(r_str)
            return pysvn.Revision( pysvn.opt_revision_kind.number, r)
        except:
            pass
    return None

def revision_exists(client, path, revision):
    try:
        client.list(path, revision=revision)
        return True
    except pysvn.ClientError:
        return False

def revision_is_dir(client, path, revision):
    """Returns True if the given path+revision is a directory.
    @raises a pysvn.ClientError if it does not exist.
    """
    # XXX I *think* the first element of the list is the requested object, and
    # subsequent items are its possible children (so ignore them).
    list_object, _ = client.list(path, revision=revision)[0]
    # list_object is a PySvnList object
    return list_object.kind == pysvn.node_kind.dir

class PysvnListStatWrapper:
    '''Wrap a pysvn listing object to look somewhat like a result of
       os.stat.
    '''
    def __init__(self, pysvn_list):
        self.pysvn_list = pysvn_list

    def __getattr__(self, name):
        try:
            if name == 'st_mode':
                # Special magic needed.
                if self.pysvn_list.kind == pysvn.node_kind.dir:
                    return stat.S_IFDIR
                else:
		    return stat.S_IFREG
                return value
            return getattr(self.pysvn_list,
                           {'st_mtime': 'time',
                            'st_size': 'size',
                           }[name])
        except AttributeError, KeyError:
            raise AttributeError, name
