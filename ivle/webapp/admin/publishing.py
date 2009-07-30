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

from ivle.database import Offering, ProjectSet, Project, Subject, User

from ivle.webapp import ApplicationRoot
from ivle.webapp.publisher import ROOT
from ivle.webapp.publisher.decorators import forward_route, reverse_route

@forward_route(ApplicationRoot, argc=1)
def root_to_user(root, segment):
    if not segment.startswith('~'):
        return None
    return User.get_by_login(root.store, segment[1:])

@forward_route(ApplicationRoot, 'subjects', argc=1)
def root_to_subject(root, name):
    return root.store.find(Subject, short_name=name).one()

@forward_route(Subject, argc=2)
def subject_to_offering(subject, year, semester):
    return subject.offering_for_semester(year, semester)

@forward_route(Offering, '+projects', argc=1)
def offering_to_project(offering, name):
    return Store.of(offering).find(Project,
                                   Project.project_set_id == ProjectSet.id,
                                   ProjectSet.offering == offering).one()

@forward_route(Offering, '+projectsets', argc=1)
def offering_to_projectset(offering, name):
    return Store.of(offering).find(ProjectSet,
                                   ProjectSet.offering == offering).one()

@reverse_route(User)
def user_url(user):
    return (ROOT, '~' + user)

@reverse_route(Subject)
def subject_url(subject):
    return (ROOT, ('subjects', subject.name))

@reverse_route(Offering)
def offering_url(offering):
    return (offering.subject, (offering.semester.year,
                               offering.semester.semester))

@reverse_route(ProjectSet)
def projectset_url(project_set):
    return (project_set.offering, ('+projectsets', project_set.name))

@reverse_route(Project)
def project_url(project):
    return (project.project_set.offering, ('+projects', project.name))
