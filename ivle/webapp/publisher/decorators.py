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

"""Decorators to annotate publishing functions."""

class forward_route(object):
    def __init__(self, src, segment=None, argc=0, viewset=None):
        self.src = src
        self.segment = segment
        self.argc = argc
        self.viewset = viewset

    def __call__(self, func):
        func._forward_route_meta = {'src': self.src,
                                    'segment': self.segment,
                                    'argc': self.argc,
                                    'viewset': self.viewset
                                    }
        return func

class reverse_route(object):
    def __init__(self, src):
        self.src = src

    def __call__(self, func):
        func._reverse_route_src = self.src
        return func
