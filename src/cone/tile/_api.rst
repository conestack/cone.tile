Prepare Tests::

    >>> from pyramid import testing
    >>> request = testing.DummyRequest()
    >>> registry = request.registry
    >>> request.registry.settings = {'debug_authorization': True}
    >>> class Model(testing.DummyResource):
    ...     path = [None]
    >>> model = Model()
    
    >>> from pyramid.interfaces import IDebugLogger
    >>> class DummyLogger(object):
    ...     def __init__(self):
    ...         self.messages = []
    ...     def info(self, msg):
    ...         self.messages.append(msg)
    ...     def error(self, msg):
    ...         self.messages.append(msg)
    ...     warn = info
    ...     debug = info
    
    >>> logger = DummyLogger()
    >>> registry.registerUtility(logger, IDebugLogger)

    >>> from cone.tile import Tile
    >>> from cone.tile import TileRenderer
    >>> from cone.tile import render_tile
    >>> from cone.tile import registerTile
    >>> from cone.tile import tile

The Tile object. Normally not created directly, this is done due registration,
see below::

    >>> mytile = Tile('cone.tile:testdata/tile1.pt', 'render', 'foo')
    >>> mytile(model,  request)
    u'<span>Tile One</span>'

Register a tile. When no object is given, the default Tile is instanciated.
``_level=1`` is needed for the doctest only to reduce the module level::

    >>> registerTile('tileone', 'testdata/tile1.pt', _level=1)

Render registered tile - first how it works in templates::

    >>> tilerenderer = TileRenderer(model, request)
    >>> tilerenderer('tileone')
    u'<span>Tile One</span>'
    
For simplification in Python code the same can be achieved by::

    >>> render_tile(model, request, 'tileone')
    u'<span>Tile One</span>'

Override tile::

    >>> registerTile('tileone', 'testdata/tile1_override.pt', _level=1)
    >>> render_tile(model, request, 'tileone')
    u'<span>Tile One Override</span>'

By default, render error message if tile ComponentLookupError::

    >>> render_tile(model, request, 'inexistent')
    u"Tile with name 'inexistent' not found:<br /><pre>((&lt;__builtin__.Model 
    instance at ...&gt;, &lt;pyramid.testing.DummyRequest object at ...&gt;), 
    &lt;InterfaceClass cone.tile._api.ITile&gt;, 'inexistent')</pre>"

To change the above behavior, the ``catch_errors`` argument can be changed to
``False``, thus preventing error swallowing::

    >>> render_tile(model, request, 'inexistent', catch_errors=False)
    Traceback (most recent call last):
      ...
    ComponentLookupError: ((<__builtin__.Model instance at ...>,
    <pyramid.testing.DummyRequest object at ...>), <InterfaceClass
    cone.tile._api.ITile>, 'inexistent')

Now the decorator (ignore the ``_level``)::

    >>> @tile('tiletwo', 'testdata/tile2.pt', _level=1)
    ... class TileTwo(Tile):
    ...     data = u'custom'
    
    >>> render_tile(model, request, 'tiletwo')
    u'<span>Tile Two: <b><span>Tile One Override</span></b></span>\n<span>custom</span>'

Optional kw arg ``attribute`` can be given which is responsible to render the
tile instead of defining a template. By default ``render`` is taken::
    
    >>> @tile('attrtile')
    ... class TileDefaultRenderAttr(Tile):
    ...     def render(self):
    ...         return u'<h1>Rendered via attribute call</h1>'
    
    >>> render_tile(model, request, 'attrtile')
    u'<h1>Rendered via attribute call</h1>'
    
    >>> @tile('foobarattrtile', attribute='foobar')
    ... class TileFoobarRenderAttr(Tile):
    ...     def foobar(self):
    ...         return u'<h1>Rendered via attribute foobar call</h1>'
    
    >>> render_tile(model, request, 'foobarattrtile')
    u'<h1>Rendered via attribute foobar call</h1>'

Default ``render`` raises NotImplementedError::

    >>> @tile('norender')
    ... class NotImplementedTile(Tile):
    ...     pass
    
    >>> render_tile(model, request, 'norender')
    Traceback (most recent call last):
      ...
    NotImplementedError: Base Tile does not implement ``render``

Tile check for ``show`` attribute and returns empty string if it evaluates to
False::

    >>> @tile('notshowtile')
    ... class TileDefaultRenderAttr(Tile):
    ...     show = 0
    
    >>> render_tile(model, request, 'notshowtile')
    u''

Tile provides a redirect function which excepts either a string containing
The URL to redirect to or a HTTPFound instance.

This function sets request.environ['redirect'] with given value. It is
considered in ``render_template``,  ``render_template_to_response`` and
``render_to_response``::

    >>> from webob.exc import HTTPFound
    
    >>> @tile('redirecttile')
    ... class RedirectTile(Tile):
    ...     def render(self):
    ...         self.redirect(HTTPFound(location='http://example.com'))
    
    >>> render_tile(model, request, 'redirecttile')
    u''
    
    >>> request.environ['redirect']
    <HTTPFound at ... 302 Found>
    
    >>> del request.environ['redirect']
    
    >>> registerTile('redirecttiletwo', 'testdata/tile3.pt', _level=1)
    >>> render_tile(model, request, 'redirecttiletwo')
    u''
    
    >>> request.environ['redirect']
    'http://example.com/foo'
    
    >>> del request.environ['redirect']

Test ``render_template``::

    >>> from cone.tile import render_template
    >>> render_template('')
    Traceback (most recent call last):
      ...
    ValueError: Expected kwargs missing: model, request.
    
    >>> render_template('', model='foo')
    Traceback (most recent call last):
      ...
    ValueError: Expected kwargs missing: model, request.
    
    >>> render_template('', request='foo')
    Traceback (most recent call last):
      ...
    ValueError: Expected kwargs missing: model, request.
    
    >>> render_template('testdata/tile1.pt', model=model, request=request)
    Traceback (most recent call last):
      ...
    ValueError: Relative path not supported: testdata/tile1.pt
    
    >>> render_template(
    ...     'cone.tile:testdata/tile1.pt', model=model, request=request)
    u'<span>Tile One</span>'
    
    >>> request.environ['redirect'] = 'http://example.com/foo'
    >>> render_template(
    ...     'cone.tile:testdata/tile1.pt', model=model, request=request)
    u''
    
    >>> del request.environ['redirect']

Test ``render_template_to_response``::

    >>> from cone.tile import render_template_to_response
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

    >>> from cone.tile import render_to_response
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

    >>> registerTile('urltile', 'testdata/tile4.pt', _level=1)
    >>> render_tile(model, request, 'urltile')
    u'<span>http://example.com</span>\n'

Check tile securing::

    >>> from pyramid.interfaces import IAuthenticationPolicy
    >>> from pyramid.interfaces import IAuthorizationPolicy
    >>> from pyramid.authentication import CallbackAuthenticationPolicy
    >>> from pyramid.authorization import ACLAuthorizationPolicy
    >>> from pyramid.security import Everyone
    >>> from pyramid.security import Allow
    >>> from pyramid.security import Deny
    >>> from pyramid.security import ALL_PERMISSIONS

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

    >>> @tile('protected_login', permission='login')
    ... class ProtectedLogin(Tile):
    ...     def render(self):
    ...         return u'permission login'
    
    >>> render_tile(model, request, 'protected_login')
    u'permission login'

View permission protected tile rendering fails for anonymous::

    >>> @tile('protected_view', permission='view')
    ... class ProtectedView(Tile):
    ...     def render(self):
    ...         return u'permission view'
    
    >>> render_tile(model, request, 'protected_view')
    Traceback (most recent call last):
      ...
    HTTPForbidden: Unauthorized: tile <ProtectedView object at ...> failed 
    permission check

    >>> from pyramid.security import view_execution_permitted
    >>> view_execution_permitted(model, request, name='protected_view')
    <ACLDenied instance ...

Set authenticated to 'max'::

    >>> authn.unauthenticated_userid = lambda *args: 'max'

Test ``view_execution_permitted``::

    >>> from pyramid.security import view_execution_permitted
    >>> view_execution_permitted(model, request)
    <Allowed instance at ...

Authenticated users are allowed to view tiles protected by view permission::

    >>> render_tile(model, request, 'protected_view')
    u'permission view'

Edit permission protected tile rendering fails for authenticated::
    
    >>> @tile('protected_edit', permission='edit')
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

    >>> @tile('protected_delete', permission='delete')
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

    >>> @tile('protected_delete', permission='delete')
    ... class ProtectedDeleteOverride(Tile):
    ...     def render(self):
    ...         return u'permission delete override'
    >>> render_tile(model, request, 'protected_delete')
    u'permission delete override'

If tile is registered non-strict, render_tile returns empty string::
    
    >>> @tile('protected_unstrict', permission='delete', strict=False)
    ... class ProtectedUnstrict(Tile):
    ...     def render(self):
    ...         return u'unstrict'
    >>> authn.unauthenticated_userid = lambda *args: None
    >>> render_tile(model, request, 'protected_unstrict')
    u''

If an error occours in tile, do not swallow error::

    >>> @tile('raisingtile', permission='login')
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
    >>> from cone.tile import _api
    >>> _api.logger = logger
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
    ... except Exception, exc:
    ...     pass
    >>> print logger.messages[0]
    Error while rendering tile template.
    ...
      Module <doctest _api.rst[...]>, line ..., in __call__
        raise Exception('MockException')
        - Mock Supplement Info
    <BLANKLINE>
    Exception: MockException
    <BLANKLINE>
    
Cleanup::

    >>> registry.unregisterUtility(logger, IDebugLogger)
    True
    
    >>> registry.unregisterUtility(authn, IAuthenticationPolicy)
    True
    
    >>> registry.unregisterUtility(authz, IAuthorizationPolicy)
    True
