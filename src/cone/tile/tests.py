from cone.tile import register_tile
from cone.tile import render_template
from cone.tile import render_template_to_response
from cone.tile import render_tile
from cone.tile import render_to_response
from cone.tile import Tile
from cone.tile import tile
from cone.tile import TileRenderer
from plone.testing import Layer
from pyramid import testing
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.interfaces import IDebugLogger
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.security import Deny
from pyramid.security import Everyone
from pyramid.security import view_execution_permitted
from webob.exc import HTTPFound
from zope.component import ComponentLookupError
import doctest
import unittest
import venusian


class DummyVenusian(object):

    def attach(self, wrapped, callback, category=None, depth=1):
        callback(None, None, wrapped)
        return None


class DummyLogger(object):

    def __init__(self):
        self.messages = []

    def info(self, msg):
        self.messages.append(msg)

    def error(self, msg):
        self.messages.append(msg)

    warn = info
    debug = info


class Model(testing.DummyResource):
    path = [None]


class Secured(object):

    def __init__(self, registry):
        self.registry = registry

    def __enter__(self):
        # Authentication policy
        def groups_callback(name, request):
            if name == 'admin_user':
                return ['role:manager']
            if name == 'editor_user':
                return ['role:editor']
            return []

        self.authn = CallbackAuthenticationPolicy()
        self.authn.callback = groups_callback
        # Expected by pyramid.authentication.effective_principals
        self.authn.unauthenticated_userid = lambda *args: None
        self.registry.registerUtility(self.authn, IAuthenticationPolicy)

        # Authorization policy
        self.authz = ACLAuthorizationPolicy()
        self.registry.registerUtility(self.authz, IAuthorizationPolicy)

    def __exit__(self, *exc):
        self.registry.unregisterUtility(self.authn, IAuthenticationPolicy)
        self.registry.unregisterUtility(self.authz, IAuthorizationPolicy)


class TileTestLayer(Layer):

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

    def secured(self):
        return Secured(self.registry)


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
            raise Exception(msg)

    def checkOutput(self, want, got, optionflags=None):
        if optionflags is None:
            optionflags = self._optionflags
        success = self._checker.check_output(want, got, optionflags)
        if not success:
            raise Failure(self._checker.output_difference(
                Example(want),
                got, optionflags
            ))


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
        register_tile(name='tileone', path='testdata/tile1.pt')

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
        register_tile(name='tileone', path='testdata/tile1_override.pt')
        self.assertEqual(
            render_tile(model, request, 'tileone'),
            u'<span>Tile One Override</span>'
        )

        # Reset overwritten tile
        register_tile(name='tileone', path='testdata/tile1.pt')

    def test_inexistent_tile(self):
        model = Model()
        request = self.layer.new_request()

        # By default, render error message if tile ComponentLookupError
        self.checkOutput("""
        Tile with name 'inexistent' not found:<br /><pre>((&lt;cone.tile.tests.Model
        instance at ...&gt;, &lt;pyramid.testing.DummyRequest object at ...&gt;),
        &lt;InterfaceClass cone.tile._api.ITile&gt;, 'inexistent')</pre>
        """, render_tile(model, request, 'inexistent'))

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

        @tile(name='tiletwo', path='testdata/tile2.pt')
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
        try:
            @tile()
            class NoTileNameTile(Tile):
                pass

            raise Exception('Missing tile name test expected to fail')
        except ValueError as e:
            self.assertEqual(
                str(e),
                (
                    "Tile ``name`` must be either given at registration time "
                    "or set on given tile class: "
                    "<class 'cone.tile.tests.NoTileNameTile'>"
                )
            )

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
            path='testdata/tile3.pt'
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
            'testdata/tile1.pt',
            model=model,
            request=request
        )
        self.assertEqual(
            str(err),
            'Relative path not supported: testdata/tile1.pt'
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

"""
Test ``render_template_to_response``::

    >>> render_template_to_response('')
    Traceback (most recent call last):
      ...
    ValueError: Expected kwargs missing: model, request.

    >>> render_template_to_response('', model='foo')
    Traceback (most recent call last):
      ...
    ValueError: Expected kwargs missing: model, request.

    >>> render_template_to_response('', request='foo')
    Traceback (most recent call last):
      ...
    ValueError: Expected kwargs missing: model, request.

    >>> render_template_to_response(
    ...     'testdata/tile1.pt', model=model, request=request)
    Traceback (most recent call last):
      ...
    ValueError: Missing template asset: testdata/tile1.pt (...tile1.pt)

    >>> render_template_to_response(
    ...     'cone.tile:testdata/tile1.pt', model=model, request=request)
    <Response at ... 200 OK>

    >>> render_template_to_response(
    ...     'cone.tile:testdata/tmpl1.pt', model=model, request=request)
    <HTTPFound at ... 302 Found>

    >>> del request.environ['redirect']

    >>> render_template_to_response(
    ...     'cone.tile:testdata/tmpl2.pt', model=model, request=request)
    <HTTPFound at ... 302 Found>

    >>> del request.environ['redirect']

Test ``render_to_response``::

    >>> render_to_response(request, 'foo')
    <Response at ... 200 OK>

    >>> request.environ['redirect'] = 'http://example.com/foo'
    >>> render_to_response(request, 'foo')
    <HTTPFound at ... 302 Found>

    >>> request.environ['redirect'] = HTTPFound(location='http://example.com')
    >>> render_to_response(request, 'foo')
    <HTTPFound at ... 302 Found>

    >>> del request.environ['redirect']

Check ``nodeurl``::

    >>> register_tile(name='urltile', path='testdata/tile4.pt', _level=1)
    >>> render_tile(model, request, 'urltile')
    u'<span>http://example.com</span>\n'

Check tile securing.

Define ACL for model::

    >>> __acl__ = [
    ...    (Allow, 'system.Authenticated', ['view']),
    ...    (Allow, 'role:editor', ['view', 'edit']),
    ...    (Allow, 'role:manager', ['view', 'edit', 'delete']),
    ...    (Allow, Everyone, ['login']),
    ...    (Deny, Everyone, ALL_PERMISSIONS),
    ... ]

    >>> model.__acl__ = __acl__

Authentication policy::

    >>> def groups_callback(name, request):
    ...     if name == 'admin_user':
    ...         return ['role:manager']
    ...     if name == 'editor_user':
    ...         return ['role:editor']
    ...     return []

    >>> authn = CallbackAuthenticationPolicy()
    >>> authn.callback = groups_callback
    >>> registry.registerUtility(authn, IAuthenticationPolicy)

Authorization policy::

    >>> authz = ACLAuthorizationPolicy()
    >>> registry.registerUtility(authz, IAuthorizationPolicy)

No authenticated user::

    >>> authn.unauthenticated_userid = lambda *args: None

Login permission protected tile can be rendered::

    >>> @tile(name='protected_login', permission='login')
    ... class ProtectedLogin(Tile):
    ...     def render(self):
    ...         return u'permission login'

    >>> render_tile(model, request, 'protected_login')
    u'permission login'

View permission protected tile rendering fails for anonymous::

    >>> @tile(name='protected_view', permission='view')
    ... class ProtectedView(Tile):
    ...     def render(self):
    ...         return u'permission view'

    >>> render_tile(model, request, 'protected_view')
    Traceback (most recent call last):
      ...
    HTTPForbidden: Unauthorized: tile <ProtectedView object at ...> failed 
    permission check

    >>> view_execution_permitted(model, request, name='protected_view')
    <ACLDenied instance ...

Set authenticated to 'max'::

    >>> authn.unauthenticated_userid = lambda *args: 'max'

Authenticated users are allowed to view tiles protected by view permission::

    >>> render_tile(model, request, 'protected_view')
    u'permission view'

Edit permission protected tile rendering fails for authenticated::

    >>> @tile(name='protected_edit', permission='edit')
    ... class ProtectedEdit(Tile):
    ...     def render(self):
    ...         return u'permission edit'

    >>> render_tile(model, request, 'protected_edit')
    Traceback (most recent call last):
      ...
    HTTPForbidden: Unauthorized: tile <ProtectedEdit object at ...> failed 
    permission check

Set authenticated to 'editor_user'::

    >>> authn.unauthenticated_userid = lambda *args: 'editor_user'

Editor is allowed to render edit permission protected tiles::

    >>> render_tile(model, request, 'protected_edit')
    u'permission edit'

Delete permission protected tile rendering fails for editor::

    >>> @tile(name='protected_delete', permission='delete')
    ... class ProtectedDelete(Tile):
    ...     def render(self):
    ...         return u'permission delete'
    >>> render_tile(model, request, 'protected_delete')
    Traceback (most recent call last):
      ...
    HTTPForbidden: Unauthorized: tile <ProtectedDelete object at ...> failed 
    permission check

Set User to 'admin_user'::

    >>> authn.unauthenticated_userid = lambda *args: 'admin_user'

Admin users are allowed to render delete permission protected tiles and
others::

    >>> render_tile(model, request, 'protected_delete')
    u'permission delete'

    >>> render_tile(model, request, 'protected_edit')
    u'permission edit'

    >>> render_tile(model, request, 'protected_view')
    u'permission view'

    >>> render_tile(model, request, 'protected_login')
    u'permission login'

Override secured tile::

    >>> @tile(name='protected_delete', permission='delete')
    ... class ProtectedDeleteOverride(Tile):
    ...     def render(self):
    ...         return u'permission delete override'
    >>> render_tile(model, request, 'protected_delete')
    u'permission delete override'

If tile is registered non-strict, render_tile returns empty string::

    >>> @tile(name='protected_unstrict', permission='delete', strict=False)
    ... class ProtectedUnstrict(Tile):
    ...     def render(self):
    ...         return u'unstrict'
    >>> authn.unauthenticated_userid = lambda *args: None
    >>> render_tile(model, request, 'protected_unstrict')
    u''

If an error occours in tile, do not swallow error::

    >>> @tile(name='raisingtile', permission='login')
    ... class RaisingTile(Tile):
    ...     def render(self):
    ...         raise Exception(u'Tile is not willing to perform')
    >>> render_tile(model, request, 'raisingtile')
    Traceback (most recent call last):
      ...
    Exception: Tile is not willing to perform

Some messages were logged::

    >>> logger.messages
    [u"Unregister secured view for 
    '<InterfaceClass zope.interface.Interface>' with name 'tileone'", 
    u"Unregister tile for 
    '<InterfaceClass zope.interface.Interface>' with name 'tileone'", 
    u"Error in rendering_tile: ((<__builtin__.Model instance at ...>, 
    <pyramid.testing.DummyRequest object at ...>), 
    <InterfaceClass cone.tile._api.ITile>, 'inexistent')", 
    u"Unregister secured view for '<InterfaceClass zope.interface.Interface>' 
    with name 'protected_delete'", 
    u"Unregister tile for '<InterfaceClass zope.interface.Interface>' 
    with name 'protected_delete'", 
    'Unauthorized: tile <ProtectedUnstrict object at ...> failed 
    permission check']

Log tile raising exception is called within a template::

    >>> logger.messages = []

    >>> class TBSupplementMock(object):
    ...     def getInfo(self, as_html=0):
    ...         return '    - Mock Supplement Info'

    >>> class BugMock(object):
    ...     def __call__(self):
    ...         __traceback_supplement__ = (TBSupplementMock,)
    ...         raise Exception('MockException')

    >>> try:
    ...     render_template('cone.tile:testdata/tile_exc_bug.pt', 
    ...                     model=model, request=request, bugcall=BugMock())
    ... except Exception, e:
    ...     pass

    >>> print logger.messages[0]
    Error while rendering tile template.
    Traceback (most recent call last):
      ...
      File "<doctest _api.rst[...]>", line ..., in __call__
        raise Exception('MockException')
        - Mock Supplement Info
    Exception: MockException
    <BLANKLINE>

Cleanup::

    >>> tile.venusian = venusian

    >>> registry.unregisterUtility(logger, IDebugLogger)
    True

    >>> registry.unregisterUtility(authn, IAuthenticationPolicy)
    True

    >>> registry.unregisterUtility(authz, IAuthorizationPolicy)
    True

"""

"""
from interlude import interact
from pprint import pprint
import doctest
import unittest

optionflags = doctest.NORMALIZE_WHITESPACE | \
              doctest.ELLIPSIS | \
              doctest.REPORT_ONLY_FIRST_FAILURE

TESTFILES = [
    '_api.rst',
]

def test_suite():
    return unittest.TestSuite([
        doctest.DocFileSuite(
            file, 
            optionflags=optionflags,
            globs={'interact': interact,
                   'pprint': pprint},
        ) for file in TESTFILES
    ])
"""

if __name__ == '__main__':
    unittest.main()
