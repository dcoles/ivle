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

"""Object publishing URL utilities."""

import os.path

ROOT = object() # Marker object for the root.
INF = object()

class PublishingError(Exception):
    pass

class NotFound(PublishingError):
    """The path did not resolve to an object."""
    pass

class InsufficientPathSegments(NotFound):
    """The path led to a route that expected more arguments."""
    pass

class NoPath(PublishingError):
    """There is no path from the given object to the root."""
    pass

class RouteConflict(PublishingError):
    """A route with the same discriminator is already registered."""
    pass

def _segment_path(path):
    """Split a path into its segments, after normalisation.

       >>> _segment_path('/path/to/something')
       ['path', 'to', 'something']
       >>> _segment_path('/path/to/something/')
       ['path', 'to', 'something']
       >>> _segment_path('/')
       []
    """

    segments = os.path.normpath(path).split('/')

    # Remove empty segments caused by leading and trailing seperators.
    if segments[0] == '':
        segments.pop(0)
    if segments[-1] == '':
        segments.pop()
    return segments

class Publisher(object):
    '''Publisher to resolve and generate paths.

    Maintains a registry of forward and reverse routes, dealing with paths
    to objects and views published in the URL space.
    '''

    def __init__(self, root, default='+index', viewset=None):
        self.fmap = {} # Forward map.
        self.rmap = {} # Reverse map.
        self.smap = {}
        self.srmap = {}
        self.vmap = {}
        self.vrmap = {}
        self.root = root
        self.default = default
        self.viewset = viewset

    def add_forward(self, src, segment, func, argc):
        """Register a forward (path resolution) route."""

        if src not in self.fmap:
            self.fmap[src] = {}

        # If a route already exists with the same source and name, we have a
        # conflict. We don't like conflicts.
        if segment in self.fmap[src]:
            raise RouteConflict((src, segment, func),
                                (src, segment, self.fmap[src][segment][0]))

        self.fmap[src][segment] = (func, argc)

    def add_forward_func(self, func):
        frm = func._forward_route_meta
        self.add_forward(frm['src'], frm['segment'], func, frm['argc'])

    def add_reverse(self, src, func):
        """Register a reverse (path generation) route."""

        if src in self.rmap:
             raise RouteConflict((src, func), (src, self.rmap[src]))
        self.rmap[src] = func

    def add_reverse_func(self, func):
        self.add_reverse(func._reverse_route_src, func)

    def add_view(self, src, name, cls, viewset=None):
        """Add a named view for a class, in the specified view set."""

        if src not in self.vmap:
            self.vmap[src] = {}

        if viewset not in self.vmap[src]:
            self.vmap[src][viewset] = {}

        if src not in self.vrmap:
            self.vrmap[src] = {}

        if name in self.vmap[src][viewset] or cls in self.vrmap[src]:
            raise RouteConflict((src, name, cls, viewset),
                         (src, name, self.vmap[src][viewset][name], viewset))

        self.vmap[src][viewset][name] = cls
        self.vrmap[src][cls] = (name, viewset)

    def add_set_switch(self, segment, viewset):
        """Register a leading path segment to switch to a view set."""

        if segment in self.smap:
            raise RouteConflict((segment, viewset),
                                (segment, self.smap[segment]))

        if viewset in self.srmap:
            raise RouteConflict((segment, viewset),
                                (self.srmap[viewset], viewset))

        self.smap[segment] = viewset
        self.srmap[viewset] = segment

    def traversed_to_object(self, obj):
        """Called when the path resolver encounters an object.

        Can be overridden to perform checks on an object before
        continuing resolution. This is handy for verifying permissions.
        """
        # We do nothing by default.
        pass

    def resolve(self, path):
        """Resolve a path into an object.

        Traverses the tree of routes using the given path.
        """

        viewset = self.viewset
        todo = _segment_path(path)

        # Override the viewset if the first segment matches.
        if len(todo) > 0 and todo[0] in self.smap:
            viewset = self.smap[todo[0]]
            del todo[0]

        (obj, view, subpath) = self._traverse(todo, self.root, viewset)

        return obj, view, subpath

    def generate(self, obj, view=None, subpath=None):
        """Resolve an object into a path.

        Traverse up the tree of reverse routes, generating a path which
        resolves to the object.
        """

        # Attempt to get all the way to the top. Each reverse route should
        # return a (parent, pathsegments) tuple.
        curobj = obj
        names = []

        # None represents the root.
        while curobj not in (ROOT, self.root):
            route = self.rmap.get(type(curobj))
            if route is None:
                raise NoPath(obj, curobj)
            (curobj, newnames) = route(curobj)

            # The reverse route can return either a string of one segment,
            # or a tuple of many.
            if isinstance(newnames, basestring):
                names.insert(0, newnames)
            else:
                names = list(newnames) + list(names)

        if view is not None:
            # If we don't have the view registered for this type, we can do
            # nothing.
            if type(obj) not in self.vrmap or \
               view not in self.vrmap[type(obj)]:
                raise NoPath(obj, view)

            (viewname, viewset) = self.vrmap[type(obj)][view]

            # If the view's set isn't the default one, we need to have it in
            # the map.
            if viewset != self.viewset:
                if viewset not in self.srmap:
                    raise NoPath(obj, view)
                else:
                    names = [self.srmap[viewset]] + names

            # Generate nice URLs for the default route, if it is the last.
            if viewname != self.default:
                # Deep views may have multiple segments in their name.
                if isinstance(viewname, basestring):
                    names += [viewname]
                elif viewname[-1] == '+index' and not subpath:
                    # If the last segment of the path is the default view, we
                    # can omit it.
                    names += viewname[:-1]
                else:
                    names += viewname

        if subpath is not None:
            if isinstance(subpath, basestring):
                return os.path.join(os.path.join('/', *names), subpath)
            else:
                names += subpath
        return os.path.join('/', *names)

    def get_ancestors(self, obj):
        """Get a sequence of an object's ancestors.

        Traverse up the tree of reverse routes, taking note of all ancestors.
        """

        # Attempt to get all the way to the top. Each reverse route should
        # return a (parent, pathsegments) tuple. We don't care about
        # pathsegments in this case.
        objs = [obj]

        # None represents the root.
        while objs[0] not in (ROOT, self.root):
            route = self.rmap.get(type(objs[0]))
            if route is None:
                raise NoPath(obj, objs[0])
            objs.insert(0, route(objs[0])[0])

        return objs[1:]

    def _traverse(self, todo, obj, viewset):
        """Populate the object stack given a list of path segments.

        Traverses the forward route tree, using the given path segments.

        Intended to be used by route(), and nobody else.
        """
        while True:
            # Attempt views first, then routes.
            if type(obj) in self.vmap and \
               viewset in self.vmap[type(obj)]:
                # If there are no segments left, attempt the default view.
                # Otherwise, look for a view with the name in the first
                # remaining path segment.
                vnames = self.vmap[type(obj)][viewset]
                view = vnames.get(self.default if len(todo) == 0 else todo[0])

                if view is not None:
                    return (obj, view, tuple(todo[1:]))
                # Now we must check for deep views.
                # A deep view is one that has a name consisting of
                # multiple segments. It's messier than it could be, because
                # we also allow omission of the final segment if it is the
                # default view name.
                elif len(todo) >= 2:
                    view = vnames.get(tuple(todo[:2]))
                    if view is not None:
                        return (obj, view, tuple(todo[2:]))
                elif len(todo) == 1:
                    # Augment it with the default view name, and look it up.
                    view = vnames.get((todo[0], self.default))
                    if view is not None:
                        return (obj, view, tuple(todo[2:]))

            # If there are no segments left to use, or there are no routes, we
            # get out.
            if len(todo) == 0:
                raise NotFound(obj, '+index', ())

            if type(obj) not in self.fmap:
                raise NotFound(obj, todo[0], todo[1:])

            routenames = self.fmap[type(obj)]

            if todo[0] in routenames:
                routename = todo[0]
                # The first path segment is the route identifier, so we skip
                # it when identifying arguments.
                argoffset = 1
            elif None in routenames:
                # Attempt traversal directly (with no intermediate segment)
                # as a last resort.
                routename = None
                argoffset = 0
            else:
                raise NotFound(obj, todo[0], tuple(todo[1:]))

            route, argc = routenames[routename]

            if argc is INF:
                args = todo[argoffset:]
                todo = []
            else:
                args = todo[argoffset:argc + argoffset]
                todo = todo[argc + argoffset:]

            if argc is not INF and len(args) != argc:
                # There were too few path segments left. Die.
                raise InsufficientPathSegments(
                                obj,
                                tuple(args) if len(args) != 1 else args[0],
                                tuple(todo)
                                )

            newobj = route(obj, *args)

            if newobj is None:
                raise NotFound(obj, tuple(args) if len(args) != 1 else args[0],
                               tuple(todo))

            self.traversed_to_object(newobj)

            obj = newobj

