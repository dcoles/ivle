# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
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

"""Utility functions for filesystem views."""

def make_path_segments(path, revno=None):
    """Split a path into a linkified HTML representation of its segments."""

    href_path = '/files'
    nav_path = ""

    pathlist = path.split("/")
    paths = []
    for path_seg in pathlist:
        if path_seg == "":
            continue
        new_seg = {}

        nav_path = nav_path + path_seg
        href_path = href_path + '/' + path_seg

        new_seg['path'] = path_seg
        new_seg['nav_path'] = nav_path
        new_seg['href_path'] = href_path
        if revno is not None:
            new_seg['href_path'] += '?r=%d' % revno

        paths.append(new_seg)
    return paths
