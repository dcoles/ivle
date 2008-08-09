#!/usr/bin/env python
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

# Program: enrol
# Author:  William Grant
# Date:    08/08/2008

# Script to enrol a user in an offering.

import common.db

import sys

if len(sys.argv) != 5:
    print >> sys.stderr, "usage: %s <login> <subjectcode> <semester> <year>" \
                         % sys.argv[0]
    sys.exit(1)

if not common.db.DB().add_enrolment(*sys.argv[1:]):
    print >> sys.stderr, "enrolment failed!"
    sys.exit(1)
