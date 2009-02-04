import urllib

from ivle.webapp.base.views import RESTView, JSONRESTView, named_operation
from ivle.webapp.errors import BadRequest, MethodNotAllowed
from ivle.webapp.testing import FakeUser, FakeRequest

class JSONRESTViewTestWithoutPUT(JSONRESTView):
    '''A small JSON REST view for testing purposes, without a PUT method.'''
    def GET(self, req):
        return {'method': 'get'}

    def PATCH(self, req, data):
        return {'method': 'patch',
                'result': data['result'], 'test': data['test']}

    @named_operation
    def do_stuff(self, what):
        return {'result': 'Did %s!' % what}

class JSONRESTViewTest(JSONRESTViewTestWithoutPUT):
    '''A small JSON REST view for testing purposes.'''
    def PUT(self, req, data):
        return {'method': 'put',
                'result': data['result'], 'test': data['test']}

class TestJSONRESTView:
    def testGET(self):
        req = FakeRequest()
        view = JSONRESTViewTest(req)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == '{"method": "get"}\n'

    def testPUT(self):
        req = FakeRequest()
        req.method = 'PUT'
        req.request_body = '{"test": "FAI\\uA746ED", "result": 1}'
        view = JSONRESTViewTest(req)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == \
                '{"test": "FAI\\ua746ED", "method": "put", "result": 1}\n'

    def testPATCH(self):
        req = FakeRequest()
        req.method = 'PATCH'
        req.request_body = '{"test": "FAI\\uA746ED", "result": 1}'
        view = JSONRESTViewTest(req)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == \
                '{"test": "FAI\\ua746ED", "method": "patch", "result": 1}\n'

    def testEmulatedPATCH(self):
        req = FakeRequest()
        req.method = 'PUT'
        req.headers_in['X-IVLE-Patch-Semantics'] = 'yes'
        req.request_body = '{"test": "FAI\\uA746ED", "result": 1}'
        view = JSONRESTViewTest(req)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == \
                '{"test": "FAI\\ua746ED", "method": "patch", "result": 1}\n'

    def testInvalidMethod(self):
        req = FakeRequest()
        req.method = 'FAKEANDBOGUS'
        view = JSONRESTViewTest(req)
        try:
            view.render(req)
        except MethodNotAllowed, e:
            assert e.allowed == ['GET', 'PUT', 'PATCH', 'POST']
        else:
            raise AssertionError("did not raise MethodNotAllowed")

    def testNoPUTMethod(self):
        req = FakeRequest()
        req.method = 'PUT'
        view = JSONRESTViewTestWithoutPUT(req)
        try:
            view.render(req)
        except MethodNotAllowed, e:
            assert e.allowed == ['GET', 'PATCH', 'POST']
        else:
            raise AssertionError("did not raise MethodNotAllowed")

    def testInvalidMethodWithPATCHEmulation(self):
        req = FakeRequest()
        req.method = 'FAKEANDBOGUS'
        req.headers_in['X-IVLE-Patch-Semantics'] = 'yes'
        view = JSONRESTViewTest(req)
        try:
            view.render(req)
        except MethodNotAllowed:
            pass
        else:
            raise AssertionError("did not raise MethodNotAllowed")

    def testNamedOperation(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'do_stuff',
                                             'what': 'blah'})
        view = JSONRESTViewTest(req)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == '{"result": "Did blah!"}\n'

    def testPOSTWithoutName(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'what': 'blah'})
        view = JSONRESTViewTest(req)
        try:
            view.render(req)
        except BadRequest, e:
            assert e.message == 'No named operation specified.'
        else:
            raise AssertionError("did not raise BadRequest")

    def testNonexistentNamedOperation(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'enoent'})
        view = JSONRESTViewTest(req)
        try:
            view.render(req)
        except BadRequest, e:
            assert e.message == 'Invalid named operation.'
        else:
            raise AssertionError("did not raise BadRequest")

    def testDisallowedNamedOperation(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'GET'})
        view = JSONRESTViewTest(req)
        try:
            view.render(req)
        except BadRequest, e:
            assert e.message == 'Invalid named operation.'
        else:
            raise AssertionError("did not raise BadRequest")

    def testNamedOperationWithMissingArgs(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'do_stuff',
                                             'nothing': 'wrong'})
        view = JSONRESTViewTest(req)
        try:
            view.render(req)
        except BadRequest, e:
            assert e.message == 'Missing arguments: what'
        else:
            raise AssertionError("did not raise BadRequest")
