import urllib

from ivle.webapp.base.rest import (JSONRESTView, named_operation,
                                   require_permission)
from ivle.webapp.errors import BadRequest, MethodNotAllowed, Unauthorized
from ivle.webapp.testing import FakeUser, FakeRequest

class JSONRESTViewTestWithoutPUT(JSONRESTView):
    '''A small JSON REST view for testing purposes, without a PUT method.'''
    def get_permissions(self, user):
        if user.login == u'fakeuser':
            return set(['view', 'edit'])
        if user.login == u'otheruser':
            return set(['view'])
        return set()

    @require_permission('view')
    def GET(self, req):
        return {'method': 'get'}

    @require_permission('edit')
    def PATCH(self, req, data):
        return {'method': 'patch',
                'result': data['result'], 'test': data['test']}

    @named_operation('view')
    def do_stuff(self, req, what):
        return {'result': 'Did %s!' % what}

    @named_operation('edit')
    def say_something(self, req, thing='nothing'):
        return {'result': 'Said %s!' % thing}

    @named_operation('edit')
    def do_say_something(self, req, what, thing='nothing'):
        return {'result': 'Said %s and %s!' % (what, thing)}

    @named_operation('view')
    def get_req_method(self, req):
        return {'method': req.method}

class JSONRESTViewTest(JSONRESTViewTestWithoutPUT):
    '''A small JSON REST view for testing purposes.'''
    @require_permission('edit')
    def PUT(self, req, data):
        return {'method': 'put',
                'result': data['result'], 'test': data['test']}

class TestJSONRESTView:
    def testGET(self):
        req = FakeRequest()
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == '{"method": "get"}\n'

    def testPUT(self):
        req = FakeRequest()
        req.method = 'PUT'
        req.request_body = '{"test": "FAI\\uA746ED", "result": 1}'
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == \
                '{"test": "FAI\\ua746ED", "method": "put", "result": 1}\n'

    def testPATCH(self):
        req = FakeRequest()
        req.method = 'PATCH'
        req.request_body = '{"test": "FAI\\uA746ED", "result": 1}'
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == \
                '{"test": "FAI\\ua746ED", "method": "patch", "result": 1}\n'

    def testEmulatedPATCH(self):
        req = FakeRequest()
        req.method = 'PUT'
        req.headers_in['X-IVLE-Patch-Semantics'] = 'yes'
        req.request_body = '{"test": "FAI\\uA746ED", "result": 1}'
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == \
                '{"test": "FAI\\ua746ED", "method": "patch", "result": 1}\n'

    def testInvalidMethod(self):
        req = FakeRequest()
        req.method = 'FAKEANDBOGUS'
        view = JSONRESTViewTest(req, None)
        try:
            view.render(req)
        except MethodNotAllowed, e:
            assert e.allowed == ['GET', 'PUT', 'PATCH', 'POST']
        else:
            raise AssertionError("did not raise MethodNotAllowed")

    def testNoPUTMethod(self):
        req = FakeRequest()
        req.method = 'PUT'
        view = JSONRESTViewTestWithoutPUT(req, None)
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
        view = JSONRESTViewTest(req, None)
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
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == '{"result": "Did blah!"}\n'

    def testPOSTWithoutName(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'what': 'blah'})
        view = JSONRESTViewTest(req, None)
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
        view = JSONRESTViewTest(req, None)
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
        view = JSONRESTViewTest(req, None)
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
        view = JSONRESTViewTest(req, None)
        try:
            view.render(req)
        except BadRequest, e:
            assert e.message == 'Missing arguments: what'
        else:
            raise AssertionError("did not raise BadRequest")

    def testNamedOperationWithExtraArgs(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'do_stuff',
                                             'what': 'blah',
                                             'toomany': 'args'})
        view = JSONRESTViewTest(req, None)
        try:
            view.render(req)
        except BadRequest, e:
            assert e.message == 'Extra arguments: toomany'
        else:
            raise AssertionError("did not raise BadRequest")

    def testNamedOperationWithDefaultArgs(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'say_something'})
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == '{"result": "Said nothing!"}\n'

    def testNamedOperationWithOverriddenDefaultArgs(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'say_something',
                                             'thing': 'something'})
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == '{"result": "Said something!"}\n'

    def testNamedOperationWithDefaultAndMissingArgs(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'do_say_something',
                                             'thing': 'something'})
        view = JSONRESTViewTest(req, None)
        try:
            view.render(req)
        except BadRequest, e:
            assert e.message == 'Missing arguments: what'
        else:
            raise AssertionError("did not raise BadRequest")

    def testNamedOperationUsingRequest(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'get_req_method'})
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == '{"method": "POST"}\n'

    def testInvalidPOSTData(self):
        req = FakeRequest()
        req.method = 'POST'
        req.request_body = 'I am invalid&&&&'
        view = JSONRESTViewTest(req, None)
        try:
            view.render(req)
        except BadRequest, e:
            print e.message
            assert e.message == 'No named operation specified.'
        else:
            raise AssertionError("did not raise BadRequest")

    def testInvalidPATCHData(self):
        req = FakeRequest()
        req.method = 'PATCH'
        req.request_body = 'I am invalid'
        view = JSONRESTViewTest(req, None)
        try:
            view.render(req)
        except BadRequest, e:
            assert e.message == 'Invalid JSON data'
        else:
            raise AssertionError("did not raise BadRequest")

    def testInvalidPUTData(self):
        req = FakeRequest()
        req.method = 'PUT'
        req.request_body = 'I am invalid'
        view = JSONRESTViewTest(req, None)
        try:
            view.render(req)
        except BadRequest, e:
            assert e.message == 'Invalid JSON data'
        else:
            raise AssertionError("did not raise BadRequest")

class TestJSONRESTSecurity:
    def testGoodMethod(self):
        req = FakeRequest()
        req.user.login = u'otheruser'
        req.method = 'GET'
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == '{"method": "get"}\n'

    def testBadMethod(self):
        req = FakeRequest()
        req.user.login = u'otheruser'
        req.method = 'PUT'
        view = JSONRESTViewTest(req, None)
        try:
            view.render(req)
        except Unauthorized, e:
            pass
        else:
            raise AssertionError("did not raise Unauthorized")

    def testGoodNamedOperation(self):
        req = FakeRequest()
        req.user.login = u'otheruser'
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'do_stuff',
                                             'what': 'blah'})
        view = JSONRESTViewTest(req, None)
        view.render(req)
        assert req.content_type == 'application/json'
        assert req.response_body == '{"result": "Did blah!"}\n'

    def testBadNamedOperation(self):
        req = FakeRequest()
        req.user.login = u'otheruser'
        req.method = 'POST'
        req.request_body = urllib.urlencode({'ivle.op': 'say_something'})
        view = JSONRESTViewTest(req, None)
        try:
            view.render(req)
        except Unauthorized, e:
            pass
        else:
            raise AssertionError("did not raise Unauthorized")

