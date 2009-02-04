from ivle.webapp.base.views import RESTView, JSONRESTView
from ivle.webapp.errors import BadRequest
from ivle.webapp.testing import FakeUser, FakeRequest

class JSONRESTViewTest(JSONRESTView):
    '''A small JSON REST view for testing purposes.'''
    def GET(self, req):
        return {'method': 'get'}

    def PUT(self, req, data):
        return {'method': 'put',
                'result': data['result'], 'test': data['test']}

    def PATCH(self, req, data):
        return {'method': 'patch',
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
        except BadRequest:
            pass
        else:
            raise AssertionError("did not raise BadRequest")

    def testInvalidMethodWithPATCHEmulation(self):
        req = FakeRequest()
        req.method = 'FAKEANDBOGUS'
        req.headers_in['X-IVLE-Patch-Semantics'] = 'yes'
        view = JSONRESTViewTest(req)
        try:
            view.render(req)
        except BadRequest:
            pass
        else:
            raise AssertionError("did not raise BadRequest")
