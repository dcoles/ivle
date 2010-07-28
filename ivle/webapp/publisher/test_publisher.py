from nose.tools import assert_equal, raises

from ivle.webapp.publisher import (INF, InsufficientPathSegments, NoPath,
                                   NotFound, RouteConflict, Publisher, ROOT)

class Root(object):
    def __init__(self):
        self.subjects = {}
        self.users = {}

    def add_subject(self, subject):
        self.subjects[subject.name] = subject

    def add_user(self, user):
        self.users[user.login] = user

class User(object):
    def __init__(self, login):
        self.login = login

class Subject(object):
    def __init__(self, name, code):
        self.name = name
        self.code = code
        self.offerings = {}

    def add_offering(self, offering):
        assert self.name == offering.subject.name
        self.offerings[(offering.year, offering.semester)] = offering

class Offering(object):
    def __init__(self, subject, year, semester):
        self.subject = subject
        self.year = year
        self.semester = semester
        self.projects = {}

    def add_project(self, project):
        assert project.offering is self
        self.projects[project.name] = project

class OfferingFiles(object):
    def __init__(self, offering):
        self.offering = offering

class OfferingFile(object):
    def __init__(self, offeringfiles, path):
        self.offering = offeringfiles.offering
        self.path = path

class Project(object):
    def __init__(self, offering, name):
        self.offering = offering
        self.name = name


class View(object):
    def __init__(self, context):
        self.context = context

class RootIndex(View):
    pass

class UserServeView(View):
    pass

class SubjectIndex(View):
    pass

class SubjectEdit(View):
    pass

class OfferingIndex(View):
    pass

class OfferingEdit(View):
    pass

class OfferingAPIIndex(View):
    pass

class OfferingFilesIndex(View):
    pass

class OfferingFileIndex(View):
    pass

class ProjectIndex(View):
    pass

class OfferingProjects(View):
    pass

class OfferingAddProject(View):
    pass

class OfferingWorksheets(View):
    pass

class OfferingWorksheetMarks(View):
    pass

class OfferingWorksheetCSVMarks(View):
    pass

def root_to_subject_or_user(root, name):
    if name.startswith('~'):
        return root.users.get(name[1:])
    return root.subjects.get(name)

def subject_to_offering(subject, year, semester):
    return subject.offerings.get((int(year), int(semester)))

def offering_to_files(offering):
    return OfferingFiles(offering)

def offering_files_to_file(offeringfiles, *path):
    return OfferingFile(offeringfiles, path)

def offering_to_project(offering, name):
    return offering.projects.get(name)

def subject_url(subject):
    return (ROOT, subject.name)

def offering_url(offering):
    return (offering.subject, (str(offering.year), str(offering.semester)))

def offering_files_url(offeringfiles):
    return (offeringfiles.offering, '+files')

def project_url(project):
    return (project.offering, ('+projects', project.name))

class BaseTest(object):
    def setUp(self):
        r = Root()
        self.r = r

        # A user would be nice.
        r.add_user(User('jsmith'))

        # Give us some subjects...
        r.add_subject(Subject('info1', '600151'))
        r.add_subject(Subject('info2', '600152'))
        r.add_subject(Subject('info3', '600251'))

        # ... and some offerings.
        r.subjects['info1'].add_offering(Offering(self.r.subjects['info1'],
                                         2008, 1))
        r.subjects['info1'].add_offering(Offering(self.r.subjects['info1'],
                                         2008, 2))
        r.subjects['info1'].add_offering(Offering(self.r.subjects['info1'],
                                         2009, 1))
        r.subjects['info2'].add_offering(Offering(self.r.subjects['info2'],
                                         2008, 2))
        r.subjects['info2'].add_offering(Offering(self.r.subjects['info2'],
                                         2009, 1))
        r.subjects['info3'].add_offering(Offering(self.r.subjects['info3'],
                                         2009, 1))

        # A normal project...
        r.subjects['info1'].offerings[(2009, 1)].add_project(
            Project(r.subjects['info1'].offerings[(2009, 1)], 'p1')
            )

        # And one conflicting with a deep view, just to be nasty.
        r.subjects['info1'].offerings[(2009, 1)].add_project(
            Project(r.subjects['info1'].offerings[(2009, 1)], '+new')
            )

class TestResolution(BaseTest):
    def setUp(self):
        super(TestResolution, self).setUp()
        self.rtr = Publisher(root=self.r, viewset='browser')
        self.rtr.add_set_switch('api', 'api')
        self.rtr.add_forward(Root, None, root_to_subject_or_user, 1)
        self.rtr.add_forward(Subject, None, subject_to_offering, 2)
        self.rtr.add_forward(Offering, '+files', offering_to_files, 0)
        self.rtr.add_forward(OfferingFiles, None, offering_files_to_file, INF)
        self.rtr.add_forward(Offering, '+projects', offering_to_project, 1)
        self.rtr.add_view(User, None, UserServeView, viewset='browser')
        self.rtr.add_view(Subject, '+index', SubjectIndex, viewset='browser')
        self.rtr.add_view(Subject, '+edit', SubjectEdit, viewset='browser')
        self.rtr.add_view(Offering, '+index', OfferingIndex, viewset='browser')
        self.rtr.add_view(Offering, '+index', OfferingAPIIndex, viewset='api')
        self.rtr.add_view(OfferingFiles, '+index', OfferingFilesIndex,
                          viewset='browser')
        self.rtr.add_view(OfferingFile, '+index', OfferingFileIndex,
                          viewset='browser')
        self.rtr.add_view(Project, '+index', ProjectIndex, viewset='browser')
        self.rtr.add_view(Offering, ('+projects', '+new'), OfferingAddProject,
                          viewset='browser')
        self.rtr.add_view(Offering, ('+projects', '+index'), OfferingProjects,
                          viewset='browser')
        self.rtr.add_view(Offering, ('+worksheets', '+index'),
                          OfferingWorksheets, viewset='browser')
        self.rtr.add_view(Offering, ('+worksheets', '+marks', '+index'),
                          OfferingWorksheetMarks, viewset='browser')
        self.rtr.add_view(Offering, ('+worksheets', '+marks', 'marks.csv'),
                          OfferingWorksheetCSVMarks, viewset='browser')

    def testOneRoute(self):
        assert_equal(self.rtr.resolve('/info1'),
                     (self.r.subjects['info1'], SubjectIndex, ())
                     )
        assert_equal(self.rtr.resolve('/info3'),
                     (self.r.subjects['info3'], SubjectIndex, ())
                     )

    def testTwoRoutes(self):
        assert_equal(self.rtr.resolve('/info1/2009/1'),
             (self.r.subjects['info1'].offerings[(2009, 1)], OfferingIndex, ())
             )
        assert_equal(self.rtr.resolve('/info2/2008/2'),
             (self.r.subjects['info2'].offerings[(2008, 2)], OfferingIndex, ())
             )

    def testNamedRoute(self):
        assert_equal(type(self.rtr.resolve('/info1/2009/1/+files')[0]),
                     OfferingFiles
                    )
        assert_equal(self.rtr.resolve('/info1/2009/1/+files')[0].offering,
                     self.r.subjects['info1'].offerings[(2009, 1)]
                    )

    def testNonDefaultView(self):
        assert_equal(self.rtr.resolve('/info1/+edit'),
                     (self.r.subjects['info1'], SubjectEdit, ())
                     )

    def testDefaultView(self):
        assert_equal(self.rtr.resolve('/info1'),
                     (self.r.subjects['info1'], SubjectIndex, ())
                     )

    def testViewWithSubpath(self):
        assert_equal(self.rtr.resolve('/info1/+edit/foo/bar'),
                     (self.r.subjects['info1'], SubjectEdit, ('foo', 'bar'))
                     )

    def testNoDefaultView(self):
        try:
            self.rtr.default = 'not+index'
            self.rtr.resolve('/info1')
        except NotFound, e:
            assert_equal(e.args, (self.r.subjects['info1'], '+index', ()))
        except:
            raise
        else:
            raise AssertionError('did not raise NotFound')
        finally:
            self.rtr.default = '+index'

    def testMissingView(self):
        try:
            self.rtr.resolve('/info1/+foo')
        except NotFound, e:
            assert_equal(e.args, (self.r.subjects['info1'], '+foo', ()))
        except:
            raise
        else:
            raise AssertionError('did not raise NotFound')

    def testViewSetSeparation(self):
        try:
            self.rtr.resolve('/api/info1/+edit')
        except NotFound, e:
            assert_equal(e.args, (self.r.subjects['info1'], '+edit', ()))
        except:
            raise
        else:
            raise AssertionError('did not raise NotFound')

    def testRouteReturningNone(self):
        try:
            self.rtr.resolve('/info9/+index')
        except NotFound, e:
            assert_equal(e.args, (self.r, 'info9', ('+index',)))
        except:
            raise
        else:
            raise AssertionError('did not raise NotFound')

    def testRouteWithInfinitelyManyArguments(self):
        o, v, sp = self.rtr.resolve('/info1/2009/1/+files/foo/bar/baz')

        assert_equal(type(o), OfferingFile)
        assert_equal(o.path, ('foo', 'bar', 'baz'))
        assert_equal(o.offering, self.r.subjects['info1'].offerings[(2009, 1)])
        assert_equal(v, OfferingFileIndex)
        assert_equal(sp, ())

    def testMissingRoute(self):
        try:
            self.rtr.resolve('/info1/2009/1/+foo')
        except NotFound, e:
            assert_equal(e.args, (
                self.r.subjects['info1'].offerings[(2009, 1)],
                '+foo',
                ()
                ))
        except:
            raise
        else:
            raise AssertionError('did not raise NotFound')

    def testAlternateViewSetWithDefault(self):
        assert_equal(self.rtr.resolve('/info1/2009/1'),
             (self.r.subjects['info1'].offerings[(2009, 1)], OfferingIndex, ())
             )

        assert_equal(self.rtr.resolve('/api/info1/2009/1'),
          (self.r.subjects['info1'].offerings[(2009, 1)], OfferingAPIIndex, ())
          )

    def testDeepView(self):
        assert_equal(self.rtr.resolve('/info1/2009/1/+projects/+new'),
             (self.r.subjects['info1'].offerings[(2009, 1)],
              OfferingAddProject, ())
             )

    def testDefaultDeepView(self):
        assert_equal(self.rtr.resolve('/info1/2009/1/+projects'),
             (self.r.subjects['info1'].offerings[(2009, 1)],
              OfferingProjects, ())
             )

    def testAnotherDefaultDeepView(self):
        assert_equal(self.rtr.resolve('/info1/2009/1/+worksheets'),
             (self.r.subjects['info1'].offerings[(2009, 1)],
              OfferingWorksheets, ())
             )

    def testReallyDeepView(self):
        assert_equal(
             self.rtr.resolve('/info1/2009/1/+worksheets/+marks/marks.csv'),
             (self.r.subjects['info1'].offerings[(2009, 1)],
              OfferingWorksheetCSVMarks, ())
             )

    def testDefaultReallyDeepView(self):
        assert_equal(self.rtr.resolve('/info1/2009/1/+worksheets/+marks'),
             (self.r.subjects['info1'].offerings[(2009, 1)],
              OfferingWorksheetMarks, ())
             )

    def testNamedRouteWithDeepView(self):
        assert_equal(self.rtr.resolve('/info1/2009/1/+projects/p1'),
             (self.r.subjects['info1'].offerings[(2009, 1)].projects['p1'],
              ProjectIndex, ())
             )

    def testNullPathView(self):
        """Verify that views can be placed immediately under an object.

        There are some cases in which it is useful for a view with a
        subpath to exist immediately under an object, with no name.
        """
        assert_equal(self.rtr.resolve('/~jsmith/foo/bar'),
             (self.r.users['jsmith'], UserServeView, ('foo', 'bar')))

    def testTrailingSlashResolvesToDefaultView(self):
        assert_equal(
             self.rtr.resolve('/info1/2009/1/'),
             (self.r.subjects['info1'].offerings[(2009, 1)],
              OfferingIndex, ())
             )

    def testTrailingSlashResolvesToDeepDefaultView(self):
        assert_equal(
             self.rtr.resolve('/info1/2009/1/+worksheets/+marks/'),
             (self.r.subjects['info1'].offerings[(2009, 1)],
              OfferingWorksheetMarks, ())
             )

    def testSubpathIndicatesTrailingSlash(self):
        assert_equal(
             self.rtr.resolve('/info1/2009/1/+index/'),
             (self.r.subjects['info1'].offerings[(2009, 1)],
              OfferingIndex, ('',))
             )

class TestGeneration(BaseTest):
    def setUp(self):
        super(TestGeneration, self).setUp()
        self.rtr = Publisher(root=self.r, viewset='browser')
        self.rtr.add_set_switch('api', 'api')
        self.rtr.add_reverse(Subject, subject_url)
        self.rtr.add_reverse(Offering, offering_url)
        self.rtr.add_reverse(OfferingFiles, offering_files_url)
        self.rtr.add_reverse(Project, project_url)
        self.rtr.add_view(Subject, '+index', SubjectIndex, viewset='browser')
        self.rtr.add_view(Subject, '+edit', SubjectEdit, viewset='browser')
        self.rtr.add_view(Offering, '+index', OfferingIndex, viewset='browser')
        self.rtr.add_view(Offering, '+index', OfferingAPIIndex, viewset='api')
        self.rtr.add_view(Project, '+index', ProjectIndex, viewset='browser')
        self.rtr.add_view(Offering, ('+projects', '+new'), OfferingAddProject,
                          viewset='browser')
        self.rtr.add_view(Offering, ('+projects', '+index'), OfferingProjects,
                          viewset='browser')

    def testOneLevel(self):
        assert_equal(self.rtr.generate(self.r.subjects['info1']), '/info1')

    def testTwoLevel(self):
        assert_equal(
            self.rtr.generate(self.r.subjects['info1'].offerings[(2009, 1)]),
            '/info1/2009/1'
            )
        assert_equal(
            self.rtr.generate(self.r.subjects['info2'].offerings[(2008, 2)]),
            '/info2/2008/2'
            )

    def testNamedRoute(self):
        assert_equal(self.rtr.generate(
                OfferingFiles(self.r.subjects['info1'].offerings[(2009, 1)])),
                '/info1/2009/1/+files'
            )

    def testView(self):
        assert_equal(self.rtr.generate(self.r.subjects['info1'], SubjectEdit),
                     '/info1/+edit'
                     )

    def testDefaultView(self):
        assert_equal(
            self.rtr.generate(self.r.subjects['info1'].offerings[(2009, 1)],
                              OfferingIndex
                              ),
            '/info1/2009/1'
            )

    def testViewWithSubpath(self):
        assert_equal(self.rtr.generate(self.r.subjects['info1'], SubjectEdit,
                                       ('foo', 'bar')),
                     '/info1/+edit/foo/bar'
                     )

    def testViewWithStringSubpath(self):
        assert_equal(self.rtr.generate(self.r.subjects['info1'], SubjectEdit,
                                       'foo/bar'),
                     '/info1/+edit/foo/bar'
                     )

    def testAlternateViewSetWithDefault(self):
        assert_equal(
            self.rtr.generate(self.r.subjects['info1'].offerings[(2009, 1)],
                              OfferingAPIIndex
                              ),
            '/api/info1/2009/1'
            )

    def testDeepView(self):
        assert_equal(
            self.rtr.generate(
                self.r.subjects['info1'].offerings[(2009, 1)],
                OfferingAddProject
                ),
        '/info1/2009/1/+projects/+new'
        )

    def testDefaultDeepView(self):
        assert_equal(
            self.rtr.generate(
                self.r.subjects['info1'].offerings[(2009, 1)],
                OfferingProjects
                ),
        '/info1/2009/1/+projects'
        )

    def testDefaultDeepViewWithSubpath(self):
        assert_equal(
            self.rtr.generate(
                self.r.subjects['info1'].offerings[(2009, 1)],
                OfferingProjects, ('foo', 'bar')
                ),
        '/info1/2009/1/+projects/+index/foo/bar'
        )

    def testNamedRouteWithDeepView(self):
        assert_equal(
            self.rtr.generate(
                self.r.subjects['info1'].offerings[(2009, 1)].projects['p1'],
                ProjectIndex
                ),
        '/info1/2009/1/+projects/p1'
        )

    def testRoot(self):
        assert_equal(self.rtr.generate(self.r), '/')


class TestErrors(BaseTest):
    def setUp(self):
        super(TestErrors, self).setUp()
        self.rtr = Publisher(root=self.r)
        self.rtr.add_forward(Root, None, root_to_subject_or_user, 1)
        self.rtr.add_forward(Subject, '+foo', lambda s: s.name + 'foo', 0)
        self.rtr.add_forward(Subject, None, subject_to_offering, 2)
        self.rtr.add_reverse(Subject, subject_url)
        self.rtr.add_reverse(Offering, offering_url)
        self.rtr.add_view(Offering, '+index', OfferingIndex)
        self.rtr.add_view(Offering, '+index', OfferingAPIIndex, viewset='api')
        self.rtr.add_set_switch('rest', 'rest')

    @raises(RouteConflict)
    def testForwardConflict(self):
        self.rtr.add_forward(Subject, '+foo', object(), 2)

    @raises(RouteConflict)
    def testReverseConflict(self):
        self.rtr.add_reverse(Subject, object())

    @raises(RouteConflict)
    def testViewConflict(self):
        self.rtr.add_view(Offering, '+index', object())

    @raises(RouteConflict)
    def testSetSwitchForwardConflict(self):
        self.rtr.add_set_switch('rest', 'foo')

    @raises(RouteConflict)
    def testSetSwitchReverseConflict(self):
        self.rtr.add_set_switch('bar', 'rest')

    @raises(NoPath)
    def testNoPath(self):
        self.rtr.generate(object())

    @raises(NoPath)
    def testNoSetSwitch(self):
        self.rtr.generate(self.r.subjects['info1'].offerings[(2009, 1)],
                          OfferingAPIIndex)

    @raises(NoPath)
    def testUnregisteredView(self):
        self.rtr.generate(self.r.subjects['info1'], SubjectIndex)

    @raises(NotFound)
    def testNotFound(self):
        self.rtr.resolve('/bar')

    @raises(InsufficientPathSegments)
    def testInsufficientPathSegments(self):
        self.rtr.resolve('/info1/foo')
