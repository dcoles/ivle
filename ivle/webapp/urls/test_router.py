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


def subject_to_edit_view(subject):
    return SubjectEdit(subject)

def subject_to_index_view(subject):
    return SubjectIndex(subject)

def offering_to_index_view(offering):
    return OfferingIndex(offering)

def subject_edit_url(view):
    return (view.context, '+edit')

def subject_index_url(view):
    return (view.context, '+index')

def offering_index_url(view):
    return (view.context, '+index')


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
    def testOneLevel(self):
        router = Router(root=self.r)
        router.add_forward(Root, None, root_to_subject, 1)

        assert router.resolve('/info1') == (self.r.subjects['info1'], None)
        assert router.resolve('/info3') == (self.r.subjects['info3'], None)

    def testTwoLevels(self):
        router = Router(root=self.r)
        router.add_forward(Root, None, root_to_subject, 1)
        router.add_forward(Subject, None, subject_to_offering, 2)

        assert router.resolve('/info1/2009/1') == \
               (self.r.subjects['info1'].offerings[(2009, 1)], None)
        assert router.resolve('/info2/2008/2') == \
               (self.r.subjects['info2'].offerings[(2008, 2)], None)

    def testDefaultView(self):
        router = Router(root=self.r, viewset='browser')
        router.add_set_switch('api', 'api')
        router.add_forward(Root, None, root_to_subject, 1)
        router.add_forward(Subject, None, subject_to_offering, 2)
        router.add_view(Subject, '+index', SubjectIndex, viewset='browser')
        router.add_view(Subject, '+edit', SubjectEdit, viewset='browser')
        router.add_view(Offering, '+index', OfferingIndex, viewset='browser')
        router.add_view(Offering, '+index', OfferingAPIIndex, viewset='api')

        assert router.resolve('/info1') == \
               (self.r.subjects['info1'], SubjectIndex)

        assert router.resolve('/info1/+edit') == \
               (self.r.subjects['info1'], SubjectEdit)

        try:
            router.resolve('/api/info1/+edit')
        except NotFound:
            pass
        else:
            raise AssertionError("returned view from wrong viewset")

        assert router.resolve('/info1/2009/1') == \
               (self.r.subjects['info1'].offerings[(2009, 1)], OfferingIndex)

        assert router.resolve('/api/info1/2009/1') == \
               (self.r.subjects['info1'].offerings[(2009, 1)], OfferingAPIIndex)

    def testNoDefaultView(self):
        router = Router(root=self.r)
        router.add_forward(Root, None, root_to_subject, 1)
        router.add_view(Subject, '+edit', SubjectEdit)

        assert router.resolve('/info1/+edit') == \
               (self.r.subjects['info1'], SubjectEdit)

        assert router.resolve('/info1') == (self.r.subjects['info1'], None)

    def testNoRoutesOrViews(self):
        router = Router(root=self.r)
        assert router.resolve('/blah') == (self.r, None)

class TestGeneration(BaseTest):
    def testOneLevel(self):
        router = Router(root=self.r)
        router.add_reverse(Subject, subject_url)

        assert router.generate(self.r.subjects['info1']) == '/info1'

    def testTwoLevel(self):
        router = Router(root=self.r)
        router.add_reverse(Subject, subject_url)
        router.add_reverse(Offering, offering_url)

        assert router.generate(self.r.subjects['info1'].offerings[(2009, 1)]) \
               == '/info1/2009/1'
        assert router.generate(self.r.subjects['info2'].offerings[(2008, 2)]) \
               == '/info2/2008/2'

    def testDefaultView(self):
        router = Router(root=self.r, viewset='browser')
        router.add_reverse(Subject, subject_url)
        router.add_reverse(Offering, offering_url)
        router.add_set_switch('api', 'api')
        router.add_view(Subject, '+index', SubjectIndex, viewset='browser')
        router.add_view(Subject, '+edit', SubjectEdit, viewset='browser')
        router.add_view(Offering, '+index', OfferingIndex, viewset='browser')
        router.add_view(Offering, '+index', OfferingAPIIndex, viewset='api')

        assert router.generate(self.r.subjects['info1'], SubjectIndex) \
               == '/info1'
        assert router.generate(self.r.subjects['info1'], SubjectEdit) \
               == '/info1/+edit'
        assert router.generate(self.r.subjects['info1'].offerings[(2009, 1)],
                                   OfferingIndex) == '/info1/2009/1'
        assert router.generate(self.r.subjects['info1'].offerings[(2009, 1)],
                                   OfferingAPIIndex) == '/api/info1/2009/1'


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
