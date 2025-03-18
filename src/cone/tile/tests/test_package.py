from cone.tile import register_tile
from cone.tile import render_template
from cone.tile import render_template_to_response
from cone.tile import render_tile
from cone.tile import render_to_response
from cone.tile import Tile
from cone.tile import tile
from cone.tile import TileRenderer
from pyramid import testing
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.httpexceptions import HTTPForbidden
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.interfaces import IDebugLogger
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import ACLDenied
from pyramid.security import Allow
from pyramid.security import Deny
from pyramid.security import Everyone
from pyramid.security import view_execution_permitted
from webob.exc import HTTPFound
from webob.response import Response
from zope.component import ComponentLookupError
import sys
import doctest
import unittest
import venusian


class DummyVenusian(object):

    def attach(self, wrapped, callback, category=None, depth=1):
        callback(None, None, wrapped)
        return None


class DummyLogger(object):

    def __init__(self):
        self.clear()

    def clear(self):
        self.messages = []

    def info(self, msg):
        self.messages.append(msg)

    error = info
    warn = info
    debug = info


class Model(testing.DummyResource):
    path = [None]


class TileTestLayer(object):

    def __init__(self):
        self.__name__ = self.__class__.__name__
        self.__bases__ = []

    def setUp(self):
        tile.venusian = DummyVenusian()
        # Registry
        request = self.new_request()
        self.registry = request.registry
        self.registry.settings = {'debug_authorization': True}
        # Dummy logger
        self.logger = DummyLogger()
        self.registry.registerUtility(self.logger, IDebugLogger)

    def tearDown(self):
        tile.venusian = venusian
        self.registry.unregisterUtility(self.logger, IDebugLogger)

    def new_request(self):
        return testing.DummyRequest()


class Example(object):

    def __init__(self, want):
        self.want = want + '\n'


class Failure(Exception):
    pass


class TileTestCase(unittest.TestCase):

    def __init__(self, *args, **kw):
        unittest.TestCase.__init__(self, *args, **kw)
        self._checker = doctest.OutputChecker()
        self._optionflags = (
            doctest.NORMALIZE_WHITESPACE |
            doctest.ELLIPSIS |
            doctest.REPORT_ONLY_FIRST_FAILURE
        )

    def expectError(self, exc, func, *args, **kw):
        try:
            func(*args, **kw)
        except exc as e:
            return e
        else:
            msg = 'Expected \'{}\' when calling \'{}\''.format(exc, func)
            raise Failure(msg)

    def checkOutput(self, want, got, optionflags=None):
        if optionflags is None:
            optionflags = self._optionflags
        success = self._checker.check_output(want, got, optionflags)
        if not success:
            raise Failure(self._checker.output_difference(
                Example(want),
                got, optionflags
            ))


class TestTileTestCase(TileTestCase):

    def test_expectError(self):
        def raising():
            raise Exception('error')

        err = self.expectError(Exception, raising)
        self.assertEqual(str(err), 'error')

        def not_raising():
            pass

        err = None
        try:
            self.expectError(Exception, not_raising)
        except Exception as e:
            err = e
        finally:
            self.assertTrue(isinstance(err, Failure))

    def test_checkOutput(self):
        self.checkOutput('a', 'a')

        err = None
        try:
            self.checkOutput('a', 'b')
        except Exception as e:
            err = e
        finally:
            self.assertTrue(isinstance(err, Failure))


def secured(func):
    def wrapped(self):
        registry = self.layer.registry

        # Authentication policy
        def groups_callback(name, request):
            if name == 'admin_user':
                return ['role:manager']
            if name == 'editor_user':
                return ['role:editor']
            return []

        authn = CallbackAuthenticationPolicy()
        authn.callback = groups_callback
        registry.registerUtility(authn, IAuthenticationPolicy)

        # Authorization policy
        authz = ACLAuthorizationPolicy()
        registry.registerUtility(authz, IAuthorizationPolicy)

        try:
            func(self, authn)
        finally:
            registry.unregisterUtility(authn, IAuthenticationPolicy)
            registry.unregisterUtility(authz, IAuthorizationPolicy)
    return wrapped


class TestTile(TileTestCase):
    layer = TileTestLayer()

    def test_Tile(self):
        model = Model()
        request = self.layer.new_request()

        # The Tile object. Normally not created directly, this is done due
        # registration
        mytile = Tile('cone.tile:testdata/tile1.pt', 'render', 'foo')
        self.assertEqual(mytile(model, request), u'<span>Tile One</span>')

        # Tile path and attribute can be set on subclass
        class DirectPathTile(Tile):
            path = 'cone.tile:testdata/tile1.pt'

        self.assertEqual(
            DirectPathTile()(model, request),
            u'<span>Tile One</span>'
        )

        class DirectAttributeTile(Tile):
            attribute = 'custom_render'

            def custom_render(self):
                return u'<span>Direct Attribute</span>'

        self.assertEqual(
            DirectAttributeTile()(model, request),
            u'<span>Direct Attribute</span>'
        )

    def test_register_tile(self):
        model = Model()
        request = self.layer.new_request()

        # Register a tile. When no object is given, the default Tile is
        # instanciated.
        register_tile(name='tileone', path='../testdata/tile1.pt')

        # Render registered tile - first how it works in templates
        tilerenderer = TileRenderer(model, request)
        self.assertEqual(tilerenderer('tileone'), u'<span>Tile One</span>')

        # For simplification in Python code the same can be achieved by
        self.assertEqual(
            render_tile(model, request, 'tileone'),
            u'<span>Tile One</span>'
        )

    def test_override_tile(self):
        model = Model()
        request = self.layer.new_request()

        # Override tile
        register_tile(name='tileone', path='../testdata/tile1_override.pt')
        self.assertEqual(
            render_tile(model, request, 'tileone'),
            u'<span>Tile One Override</span>'
        )

        # Reset overwritten tile
        self.layer.logger.clear()

        register_tile(name='tileone', path='../testdata/tile1.pt')

        self.checkOutput("""
        Unregister secured view for 'zope.interface.Interface'
        with name 'tileone'
        """, self.layer.logger.messages[0])

        self.checkOutput("""
        Unregister tile for 'zope.interface.Interface'
        with name 'tileone'
        """, self.layer.logger.messages[1])

        self.layer.logger.clear()

    def test_inexistent_tile(self):
        model = Model()
        request = self.layer.new_request()

        self.layer.logger.clear()

        # By default, render error message if tile ComponentLookupError
        self.checkOutput(
            "Tile with name 'inexistent' not found:<br /><pre>((&lt;cone.tile." +
            "tests.test_package.Model ... at ...&gt;, &lt;pyramid.testing." +
            "DummyRequest object at ...&gt;), &lt;InterfaceClass cone.tile." +
            "_api.ITile&gt;, ...inexistent...)</pre>",
        render_tile(model, request, 'inexistent'))
        self.checkOutput(
            "Error in rendering_tile: ((<cone.tile.tests.test_package.Model ... at ...>, " +
            "<pyramid.testing.DummyRequest object at ...>), " +
            "<InterfaceClass cone.tile._api.ITile>, 'inexistent')",
        self.layer.logger.messages[0])

        self.layer.logger.clear()

        # To change the above behavior, the ``catch_errors`` argument can be
        # changed to ``False``, thus preventing error swallowing
        self.expectError(
            ComponentLookupError,
            render_tile,
            model,
            request,
            'inexistent',
            catch_errors=False
        )

    def test_tile_decorator(self):
        model = Model()
        request = self.layer.new_request()

        @tile(name='tiletwo', path='../testdata/tile2.pt')
        class TileTwo(Tile):
            data = u'custom'

        self.assertEqual(
            render_tile(model, request, 'tiletwo'),
            (
                u'<span>Tile Two: <b><span>Tile One</span></b>'
                u'</span>\n<span>custom</span>'
            )
        )

        # ``name`` can be skipped when registering a tile given it it set on
        # the tile class directly
        @tile()
        class NameFromTile(Tile):
            name = 'name_from_tile'

            def render(self):
                return u'<span>Name from tile</span>'

        self.assertEqual(
            render_tile(model, request, 'name_from_tile'),
            u'<span>Name from tile</span>'
        )

        # Missing tile name
        err = None
        try:
            @tile()
            class NoTileNameTile(Tile):
                pass
        except ValueError as e:
            err = e
        finally:
            self.checkOutput("""
            Tile ``name`` must be either given at registration time
            or set on given tile class:
            <class 'cone.tile.tests...NoTileNameTile'>
            """, str(err))

        # Optional kw arg ``attribute`` can be given which is responsible to
        # render the tile instead of defining a template. By default ``render``
        # is taken
        @tile(name='attrtile')
        class TileDefaultRenderAttr(Tile):
            def render(self):
                return u'<h1>Rendered via attribute call</h1>'

        self.assertEqual(
            render_tile(model, request, 'attrtile'),
            u'<h1>Rendered via attribute call</h1>'
        )

        @tile(name='foobarattrtile', attribute='foobar')
        class TileFoobarRenderAttr(Tile):
            def foobar(self):
                return u'<h1>Rendered via attribute foobar call</h1>'

        self.assertEqual(
            render_tile(model, request, 'foobarattrtile'),
            u'<h1>Rendered via attribute foobar call</h1>'
        )

        # Default ``render`` raises NotImplementedError
        @tile(name='norender')
        class NotImplementedTile(Tile):
            pass

        err = self.expectError(
            NotImplementedError,
            render_tile,
            model,
            request,
            'norender'
        )
        self.assertEqual(str(err), "Base Tile does not implement ``render``")

        # Tile check for ``show`` attribute and returns empty string if it
        # evaluates to False
        @tile(name='notshowtile')
        class TileNotShown(Tile):
            show = 0

        self.assertEqual(render_tile(model, request, 'notshowtile'), u'')

    def test_redirect(self):
        # Tile provides a redirect function which excepts either a string
        # containing the URL to redirect to or a HTTPFound instance.

        # This function sets request.environ['redirect'] with given value. It
        # is considered in ``render_template``, ``render_template_to_response``
        # and ``render_to_response``
        model = Model()
        request = self.layer.new_request()

        @tile(name='redirecttile')
        class RedirectTile(Tile):
            def render(self):
                self.redirect(HTTPFound(location='http://example.com'))

        self.assertEqual(render_tile(model, request, 'redirecttile'), u'')

        http_found = request.environ['redirect']
        self.assertTrue(isinstance(http_found, HTTPFound))
        del request.environ['redirect']

        register_tile(
            name='redirecttiletwo',
            path='../testdata/tile3.pt'
        )
        self.assertEqual(render_tile(model, request, 'redirecttiletwo'), u'')
        self.assertEqual(request.environ['redirect'], 'http://example.com/foo')
        del request.environ['redirect']

    def test_render_template(self):
        model = Model()
        request = self.layer.new_request()

        err = self.expectError(
            ValueError,
            render_template,
            ''
        )
        self.assertEqual(str(err), 'Expected kwargs missing: model, request.')

        err = self.expectError(
            ValueError,
            render_template,
            '',
            model='foo'
        )
        self.assertEqual(str(err), 'Expected kwargs missing: model, request.')

        err = self.expectError(
            ValueError,
            render_template,
            '',
            request='foo'
        )
        self.assertEqual(str(err), 'Expected kwargs missing: model, request.')

        err = self.expectError(
            ValueError,
            render_template,
            '../testdata/tile1.pt',
            model=model,
            request=request
        )
        self.assertEqual(
            str(err),
            'Relative path not supported: ../testdata/tile1.pt'
        )

        rendered = render_template(
            'cone.tile:testdata/tile1.pt',
            model=model,
            request=request
        )
        self.assertEqual(rendered, u'<span>Tile One</span>')

        request.environ['redirect'] = 'http://example.com/foo'
        rendered = render_template(
            'cone.tile:testdata/tile1.pt',
            model=model,
            request=request
        )
        self.assertEqual(rendered, u'')

        del request.environ['redirect']

    def test_render_template_to_response(self):
        model = Model()
        request = self.layer.new_request()

        err = self.expectError(
            ValueError,
            render_template_to_response,
            ''
        )
        self.assertEqual(str(err), 'Expected kwargs missing: model, request.')

        err = self.expectError(
            ValueError,
            render_template_to_response,
            '',
            model='foo'
        )
        self.assertEqual(str(err), 'Expected kwargs missing: model, request.')

        err = self.expectError(
            ValueError,
            render_template_to_response,
            '',
            request='foo'
        )
        self.assertEqual(str(err), 'Expected kwargs missing: model, request.')

        err = self.expectError(
            ValueError,
            render_template_to_response,
            '../testdata/foo.pt',
            model=model,
            request=request
        )
        self.assertTrue(str(err).startswith(
            'Missing template asset: ../testdata/foo.pt'
        ))

        response = render_template_to_response(
            'cone.tile:testdata/tile1.pt',
            model=model,
            request=request
        )
        self.assertTrue(isinstance(response, Response))

        response = render_template_to_response(
            'cone.tile:testdata/tmpl1.pt',
            model=model,
            request=request
        )
        self.assertTrue(isinstance(response, HTTPFound))
        del request.environ['redirect']

        response = render_template_to_response(
            'cone.tile:testdata/tmpl2.pt',
            model=model,
            request=request
        )
        self.assertTrue(isinstance(response, HTTPFound))
        del request.environ['redirect']

    def test_render_to_response(self):
        request = self.layer.new_request()

        response = render_to_response(request, 'foo')
        self.assertTrue(isinstance(response, Response))

        request.environ['redirect'] = 'http://example.com/foo'
        response = render_to_response(request, 'foo')
        self.assertTrue(isinstance(response, HTTPFound))

        request.environ['redirect'] = HTTPFound(location='http://example.com')
        response = render_to_response(request, 'foo')
        self.assertTrue(request.environ['redirect'] is response)
        del request.environ['redirect']

    def test_nodeurl(self):
        model = Model()
        request = self.layer.new_request()

        register_tile(name='urltile', path='../testdata/tile4.pt')
        self.assertEqual(
            render_tile(model, request, 'urltile'),
            u'<span>http://example.com</span>\n'
        )

        model.path = [None, 'foo']
        self.assertEqual(
            render_tile(model, request, 'urltile'),
            u'<span>http://example.com/foo</span>\n'
        )

        model.path = [None, 'foo', 'bar/baz']
        self.assertEqual(
            render_tile(model, request, 'urltile'),
            u'<span>http://example.com/foo/bar__s_l_a_s_h__baz</span>\n'
        )

    @secured
    def test_secured(self, authn):
        @tile(name='protected_login', permission='login')
        class ProtectedLogin(Tile):
            def render(self):
                return u'permission login'

        @tile(name='protected_view', permission='view')
        class ProtectedView(Tile):
            def render(self):
                return u'permission view'

        @tile(name='protected_edit', permission='edit')
        class ProtectedEdit(Tile):
            def render(self):
                return u'permission edit'

        @tile(name='protected_delete', permission='delete')
        class ProtectedDelete(Tile):
            def render(self):
                return u'permission delete'

        model = Model()
        request = self.layer.new_request()

        # Define ACL for model
        model.__acl__ = [
            (Allow, 'system.Authenticated', ['view']),
            (Allow, 'role:editor', ['view', 'edit']),
            (Allow, 'role:manager', ['view', 'edit', 'delete']),
            (Allow, Everyone, ['login']),
            (Deny, Everyone, ALL_PERMISSIONS),
        ]

        # No authenticated user
        authn.unauthenticated_userid = lambda *args: None

        # Login permission protected tile can be rendered
        self.assertEqual(
            render_tile(model, request, 'protected_login'),
            u'permission login'
        )

        # View permission protected tile rendering fails for anonymous
        err = self.expectError(
            HTTPForbidden,
            render_tile,
            model,
            request,
            'protected_view'
        )
        self.assertTrue(str(err).find('failed permission check') > -1)

        rule = view_execution_permitted(model, request, name='protected_view')
        self.assertTrue(isinstance(rule, ACLDenied))

        # Set authenticated to 'max'
        authn.unauthenticated_userid = lambda *args: 'max'

        # Authenticated users are allowed to view tiles protected by view
        # permission
        self.assertEqual(
            render_tile(model, request, 'protected_view'),
            u'permission view'
        )

        # Edit permission protected tile rendering fails for authenticated
        err = self.expectError(
            HTTPForbidden,
            render_tile,
            model,
            request,
            'protected_edit'
        )
        self.assertTrue(str(err).find('failed permission check') > -1)

        # Set authenticated to 'editor_user'
        authn.unauthenticated_userid = lambda *args: 'editor_user'

        # Editor is allowed to render edit permission protected tiles
        self.assertEqual(
            render_tile(model, request, 'protected_edit'),
            u'permission edit'
        )

        # Delete permission protected tile rendering fails for editor
        err = self.expectError(
            HTTPForbidden,
            render_tile,
            model,
            request,
            'protected_delete'
        )
        self.assertTrue(str(err).find('failed permission check') > -1)

        # Set User to 'admin_user'
        authn.unauthenticated_userid = lambda *args: 'admin_user'

        # Admin users are allowed to render delete permission protected tiles
        # and others
        self.assertEqual(
            render_tile(model, request, 'protected_delete'),
            u'permission delete'
        )
        self.assertEqual(
            render_tile(model, request, 'protected_edit'),
            u'permission edit'
        )
        self.assertEqual(
            render_tile(model, request, 'protected_view'),
            u'permission view'
        )
        self.assertEqual(
            render_tile(model, request, 'protected_login'),
            u'permission login'
        )

        # Override secured tile
        @tile(name='protected_delete', permission='delete')
        class ProtectedDeleteOverride(Tile):
            def render(self):
                return u'permission delete override'

        self.assertEqual(
            render_tile(model, request, 'protected_delete'),
            u'permission delete override'
        )

        # If tile is registered non-strict, render_tile returns empty string
        @tile(name='protected_unstrict', permission='delete', strict=False)
        class ProtectedUnstrict(Tile):
            pass

        authn.unauthenticated_userid = lambda *args: None

        self.layer.logger.clear()

        self.assertEqual(render_tile(model, request, 'protected_unstrict'), u'')

        self.checkOutput("""
        Unauthorized: tile <cone.tile.tests...ProtectedUnstrict object at ...>
        failed permission check
        """, self.layer.logger.messages[0])

        self.layer.logger.clear()

        # If an error occours in tile, do not swallow error
        @tile(name='raisingtile', permission='login')
        class RaisingTile(Tile):
            def render(self):
                raise Exception(u'Tile is not willing to perform')

        err = self.expectError(
            Exception,
            render_tile,
            model,
            request,
            'raisingtile'
        )
        self.assertEqual(str(err), 'Tile is not willing to perform')

    # def test_traceback_supplement(self):
    #     self.layer.logger.clear()

    #     class TBSupplementMock(object):
    #         def getInfo(self, as_html=0):
    #             return '    - Mock Supplement Info'

    #     class BugMock(object):
    #         def __call__(self):
    #             __traceback_supplement__ = (TBSupplementMock,)
    #             raise Exception('MockException')

    #     try:
    #         model = Model()
    #         request = self.layer.new_request()
    #         render_template(
    #             'cone.tile:testdata/tile_exc_bug.pt',
    #             model=model,
    #             request=request,
    #             bugcall=BugMock()
    #         )
    #     except Exception:
    #         pass

    #     self.checkOutput("""
    #     Error while rendering tile template.
    #     Traceback (most recent call last):
    #       File "..._api.py", line ..., in render_template
    #         ...
    #         raise Exception('MockException')
    #         - Mock Supplement Info
    #     Exception: MockException
    #     """, self.layer.logger.messages[0])


def run_tests():
    from cone.tile import tests
    from zope.testrunner.runner import Runner

    suite = unittest.TestSuite()
    suite.addTest(unittest.findTestCases(tests))

    runner = Runner(found_suites=[suite])
    runner.run()
    sys.exit(int(runner.failed))


if __name__ == '__main__':
    run_tests()
