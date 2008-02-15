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

# Module: Capabilities
# Author: Matt Giuca
# Date:   15/2/2008

# Provides a Role class which is used for the "rolenm" field of login rows
# from the database.
# This also provides a set of Caps (capabilities) and the ability to check if
# any given role has a given capability.

class Role(object):
    """
    Role enumeration class. Provides values for "rolenm" fields, which are
    enumerable and comparable. Immutable objects.

    This allows you to check if a role has a certain capability by doing a
    >= comparison on the lowest role with that capability.

    Class Role has a capitalized member for each role, of type Role.
    eg. Role.STUDENT is a Role object describing the "student" role.
    """
    _roles = ["anyone", "student", "marker", "tutor", "lecturer", "admin"]
    _roles_to_int = {}          # Will be written after class def
    def __init__(self, role):
        """Creates a new Role object.
        role may be any of the following types:
        * Role: Copies.
        * str: Role of that name, as given by the str of a Role
            (These correspond to the entries in the "rolenm" field of the DB).
            Raises an Exception if the string is not a role.
        * int: Role of that numeric index, as given by the fromEnum of a Role.
            (This is the same as calling toEnum).
        """
        # Internally, stored as an int
        if isinstance(role, Role):
            self._role = role._role
        elif isinstance(role, str):
            try:
                self._role = Role._roles_to_int[role.lower()]
            except KeyError:
                raise Exception("Not a valid role name: %s" % repr(role))
        elif isinstance(role, int):
            if role >= 0 and role < len(Role._roles):
                self._role = role
            else:
                raise Exception("Not a valid role ID: %d" % role)
    def __str__(self):
        return Role._roles[self._role]
    def __repr__(self):
        return "Role.%s" % Role._roles[self._role].upper()
    def __cmp__(self, other):
        return self._role - other._role
    def __hash__(self):
        return hash(self._role)

    def fromEnum(self):
        """Returns the int representation of this Role."""
        return self._role
    @staticmethod
    def toEnum(num):
        """Given an int, returns the Role for that role ID."""
        return Role(num)

    def hasCap(self, capability):
        """Given a capability (which is a Role object), returns True if this
        Role has that capability, False otherwise.
        """
        return self >= capability

# Role constants. These are actually members of the Role class, but they are
# defined here because they actually have the type Role.
for i in range(0, len(Role._roles)):
    # XXX This is the only way I could find to write an attribute to a
    # new-style class. It looks very dodgy.
    type.__setattr__(Role, Role._roles[i].upper(), Role(i))
    Role._roles_to_int[Role._roles[i]] = i

# Set of capabilities, which maps global variables onto Roles.
# This provides the minimum role level required in order to perform the given
# capability.
# (So any role above the role specified can perform this cap).

CAP_CREATEUSER = Role.ADMIN
