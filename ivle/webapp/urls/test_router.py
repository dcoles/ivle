from nose.tools import assert_equal, raises

from ivle.webapp.urls import (InsufficientPathSegments, NoPath, NotFound,
                              RouteConflict, Router, ROOT)

class Root(object):
    def __init__(self):
        self.subjects = {}

    def add_subject(self, subject):
        self.subjects[subject.name] = subject

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

class View(object):
    def __init__(self, context):
        self.context = context

class RootIndex(View):
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


def root_to_subject(root, name):
    try:
        return root.subjects[name]
    except KeyError:
        raise NotFound(root, name)

def subject_to_offering(subject, year, semester):
    try:
        return subject.offerings[(int(year), int(semester))]
    except (KeyError, ValueError):
        raise NotFound(subject, (year, semester))


def subject_url(subject):
    return (ROOT, subject.name)

def offering_url(offering):
    return (offering.subject, (str(offering.year), str(offering.semester)))


class BaseTest(object):
    def setUp(self):
        r = Root()
        self.r = r

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

class TestResolution(BaseTest):
    def setUp(self):
        super(TestResolution, self).setUp()
        self.rtr = Router(root=self.r, viewset='browser')
        self.rtr.add_set_switch('api', 'api')
        self.rtr.add_forward(Root, None, root_to_subject, 1)
        self.rtr.add_forward(Subject, None, subject_to_offering, 2)
        self.rtr.add_view(Subject, '+index', SubjectIndex, viewset='browser')
        self.rtr.add_view(Subject, '+edit', SubjectEdit, viewset='browser')
        self.rtr.add_view(Offering, '+index', OfferingIndex, viewset='browser')
        self.rtr.add_view(Offering, '+index', OfferingAPIIndex, viewset='api')

    def testOneLevel(self):
        # Don't test view stuff just yet.
        try:
            self.rtr.default='not+index'
            assert_equal(self.rtr.resolve('/info1'),
                         (self.r.subjects['info1'], None)
                         )
            assert_equal(self.rtr.resolve('/info3'),
                         (self.r.subjects['info3'], None)
                         )
        finally:
            self.rtr.default='+index'

    def testTwoLevels(self):
        try:
            self.rtr.default='not+index'

            assert_equal(self.rtr.resolve('/info1/2009/1'),
                         (self.r.subjects['info1'].offerings[(2009, 1)], None)
                         )
            assert_equal(self.rtr.resolve('/info2/2008/2'),
                         (self.r.subjects['info2'].offerings[(2008, 2)], None)
                         )
        finally:
            self.rtr.default='+index'

    def testView(self):
        assert_equal(self.rtr.resolve('/info1/+edit'),
                     (self.r.subjects['info1'], SubjectEdit)
                     )

    def testDefaultView(self):
        assert_equal(self.rtr.resolve('/info1'),
                     (self.r.subjects['info1'], SubjectIndex)
                     )

    @raises(NotFound)
    def testViewSetSeparation(self):
        self.rtr.resolve('/api/info1/+edit')

    def testAlternateViewSetWithDefault(self):
        assert_equal(self.rtr.resolve('/info1/2009/1'),
               (self.r.subjects['info1'].offerings[(2009, 1)], OfferingIndex)
               )

        assert_equal(self.rtr.resolve('/api/info1/2009/1'),
               (self.r.subjects['info1'].offerings[(2009, 1)], OfferingAPIIndex)
               )

class TestGeneration(BaseTest):
    def setUp(self):
        super(TestGeneration, self).setUp()
        self.rtr = Router(root=self.r, viewset='browser')
        self.rtr.add_set_switch('api', 'api')
        self.rtr.add_reverse(Subject, subject_url)
        self.rtr.add_reverse(Offering, offering_url)
        self.rtr.add_view(Subject, '+index', SubjectIndex, viewset='browser')
        self.rtr.add_view(Subject, '+edit', SubjectEdit, viewset='browser')
        self.rtr.add_view(Offering, '+index', OfferingIndex, viewset='browser')
        self.rtr.add_view(Offering, '+index', OfferingAPIIndex, viewset='api')

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

    def testAlternateViewSetWithDefault(self):
        assert_equal(
            self.rtr.generate(self.r.subjects['info1'].offerings[(2009, 1)],
                              OfferingAPIIndex
                              ),
            '/api/info1/2009/1'
            )


class TestErrors(BaseTest):
    def setUp(self):
        super(TestErrors, self).setUp()
        self.rtr = Router(root=self.r)
        self.rtr.add_forward(Root, None, root_to_subject, 1)
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
