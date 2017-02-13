from pyramid.chameleon_zpt import ZPTTemplateRenderer
try:
    # pyramid 1.1
    from pyramid.config import preserve_view_attrs
except ImportError:                                         #pragma NO COVERAGE
    # pyramid 1.2
    from pyramid.config.views import preserve_view_attrs    #pragma NO COVERAGE
from pyramid.exceptions import Forbidden
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.interfaces import IDebugLogger
from pyramid.interfaces import IRequest
from pyramid.interfaces import IResponseFactory
from pyramid.interfaces import ISecuredView
from pyramid.interfaces import IViewClassifier
from pyramid.path import caller_package
from pyramid.renderers import RendererHelper
from pyramid.renderers import template_renderer_factory
from pyramid.threadlocal import get_current_registry
from webob import Response
from webob.exc import HTTPFound
from zope.component import ComponentLookupError
from zope.exceptions.exceptionformatter import format_exception
from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import implementer
import cgi
import logging
import os
import sys
import urllib


logger = logging.getLogger('cone.tile')


def log_exception(msg, exc, tb):
    exc_str = '\n'.join(format_exception(exc.__class__, str(exc), tb))
    logger.error('%s\n\n%s' % (msg, exc_str))


class ITile(Interface):
    """Renders some HTML snippet.
    """

    name = Attribute(u"The name under which this tile is registered.")
    show = Attribute(u"Flag wether to render the tile.")

    def __call__(model, request):
        """Renders the tile.

        It's intended to work this way: First it calls its own prepare method,
        then it checks its own show attribute. If this returns True it renders
        the template in the context of the ITile implementing class instance.
        """

    def prepare():
        """Prepares the tile.

        I.e. fetch data to display ...
        """


def _update_kw(**kw):
    if not ('request' in kw and 'model' in kw):
        raise ValueError, "Expected kwargs missing: model, request."
    kw.update({'tile': TileRenderer(kw['model'], kw['request'])})
    return kw


def _redirect(kw):
    if kw['request'].environ.get('redirect'):
        return True
    return False


def render_template(path, **kw):
    """Render template considering redirect flag.
    """
    kw = _update_kw(**kw)
    if _redirect(kw):
        return u''
    if not (':' in path or os.path.isabs(path)):
        raise ValueError, 'Relative path not supported: %s' % path
    info = RendererHelper(name=path, registry=kw['request'].registry)
    renderer = template_renderer_factory(info, ZPTTemplateRenderer)
    try:
        return renderer(kw, {})
    except Exception, exc:
        log_exception('Error while rendering tile template.', exc,
                      sys.exc_traceback)
        raise


def render_template_to_response(path, **kw):
    """Render template to response considering redirect flag.
    """
    kw = _update_kw(**kw)
    kw['request'].environ['redirect'] = None
    info = RendererHelper(name=path, registry=kw['request'].registry)
    renderer = template_renderer_factory(info, ZPTTemplateRenderer)
    result = renderer(kw, {})
    if _redirect(kw):
        redirect = kw['request'].environ['redirect']
        if isinstance(redirect, HTTPFound):
            return redirect
        return HTTPFound(location=redirect)
    response_factory = kw['request'].registry.queryUtility(IResponseFactory,
                                                           default=Response)
    return response_factory(result)


def render_to_response(request, result):
    """Render result to response considering redirect flag.
    """
    if _redirect(kw={'request': request}):
        redirect = request.environ['redirect']
        if isinstance(redirect, HTTPFound):
            return redirect
        return HTTPFound(location=redirect)
    response_factory = request.registry.queryUtility(IResponseFactory,
                                                     default=Response)
    return response_factory(result)


def render_tile(model, request, name, catch_errors=True):
    """Render a tile.

    Intended usage is in application code.

    ``model``
        application model aka context

    ``request``
        the current request

    ``name``
        name of the requested tile

    ``catch_errors``
        if set to False, ComponentLookupError will be propagated, otherwise it
        will be catched and the error message will be returned as the result
    """
    if not catch_errors:
        return request.registry.getMultiAdapter((model, request),
                                                ITile, name=name)
    try:
        return request.registry.getMultiAdapter((model, request),
                                                ITile, name=name)
    except ComponentLookupError, e:
        # XXX: ComponentLookupError appears even if another error causes tile
        #      __call__ to fail.
        settings = request.registry.settings
        if settings.get('debug_authorization', False):
            msg = u"Error in rendering_tile: %s" % str(e)
            logger = request.registry.getUtility(IDebugLogger)
            logger.debug(msg)
        return u"Tile with name '%s' not found:<br /><pre>%s</pre>" % \
               (name, cgi.escape(str(e).decode('utf-8')))


class TileRenderer(object):
    """Render a tile.

    Intended usage is as instance in template code.
    """

    def __init__(self, model, request):
        self.model, self.request = model, request

    def __call__(self, name):
        return render_tile(self.model, self.request, name)


@implementer(ITile)
class Tile(object):

    def __init__(self, path, attribute, name):
        self.name = name
        self.path = path
        self.attribute = attribute

    def __call__(self, model, request):
        self.model = model
        self.request = request
        self.prepare()
        if not self.show:
            return u''
        if self.path:
            result = render_template(self.path, request=request,
                                     model=model, context=self)
        else:
            renderer = getattr(self, self.attribute)
            result = renderer()
        if request.environ.get('redirect'):
            return u''
        return result

    @property
    def show(self):
        return True

    def prepare(self):
        pass

    def render(self):
        raise NotImplementedError('Base Tile does not implement ``render``')

    def redirect(self, redirect):
        """Given param is either a string containing a URL or a HTTPFound
        instance.

        Why do we need a redirect in a tile?

        A tile is not always rendered to the response, form tiles i.e.
        might perform redirection.
        """
        self.request.environ['redirect'] = redirect

    @property
    def nodeurl(self):
        """XXX: move out from here
        """
        #XXX: see cone.app.browser.utils, not imported in order not to
        #depend on it, as this is supposed to move anyway
        relpath = [urllib.quote(p.replace('/', '__s_l_a_s_h__')) \
                       for p in self.model.path if p is not None]
        return '/'.join([self.request.application_url] + relpath)


def _secure_tile(tile, permission, authn_policy, authz_policy, strict):
    """wraps tile and does security checks.
    """
    wrapped_tile = tile
    if not authn_policy and not authz_policy:
        return tile
    def _secured_tile(context, request):
        principals = authn_policy.effective_principals(request)
        if authz_policy.permits(context, principals, permission):
            return tile(context, request)
        msg = getattr(request, 'authdebug_message',
                      'Unauthorized: tile %s failed permission check' % tile)
        if strict:
            raise Forbidden(msg)
        settings = request.registry.settings
        if settings.get('debug_authorization', False):
            logger = request.registry.getUtility(IDebugLogger)
            logger.debug(msg)
        return u''
    _secured_tile.__call_permissive__ = tile
    def _permitted(context, request):
        principals = authn_policy.effective_principals(request)
        return authz_policy.permits(context, principals, permission)
    _secured_tile.__permitted__ = _permitted
    wrapped_tile = _secured_tile
    preserve_view_attrs(tile, wrapped_tile)
    return wrapped_tile


# Registration
def registerTile(name, path=None, attribute='render', interface=Interface,
                 class_=Tile, permission='view', strict=True, _level=2):
    """registers a tile.

    ``name``
        identifier of the tile (for later lookup).

    ``path``
        either relative path to the template or absolute path or path prefixed
        by the absolute package name delimeted by ':'. If ``path`` is used
        ``attribute`` is ignored.

    ``attribute``
        attribute on the given _class to be used to render the tile. Defaults to
        ``render``.

    ``interface``
        Interface or Class of the pyramid model the tile is registered for.

    ``class_``
        Class to be used to render the tile. usally ``cone.tile.Tile`` or a
        subclass of. Promises to implement ``cone.tile.ITile``.

    ``permission``
        Enables security checking for this tile. Defaults to ``view``. If set to
        ``None`` security checks are disabled.
    
    ``strict``
        Wether to raise ``Forbidden`` or not. Defaults to ``True``. If set to
        ``False`` the exception is consumed and an empty unicode string is
        returned.

    ``_level``
        is a bit special to make doctests pass the magic path-detection.
        you must never touch it in application code.
    """
    if path and not (':' in path or os.path.isabs(path)):
        path = '%s:%s' % (caller_package(_level).__name__, path)

    tile = class_(path, attribute, name)

    registry = get_current_registry()
    registered = registry.adapters.registered
    unregister = registry.adapters.unregister

    logger = registry.getUtility(IDebugLogger)

    if permission is not None:
        authn_policy = registry.queryUtility(IAuthenticationPolicy)
        authz_policy = registry.queryUtility(IAuthorizationPolicy)

        tile = _secure_tile(
            tile, permission, authn_policy, authz_policy, strict)

        exists = registered((IViewClassifier, IRequest, interface),
                            ISecuredView, name=name)
        if exists:
            msg = u"Unregister secured view for '%s' with name '%s'" % (
                str(interface), name)
            logger.debug(msg)
            unregister((IViewClassifier, IRequest, interface),
                       ISecuredView, name=name)

        registry.registerAdapter(
            tile,
            (IViewClassifier, IRequest, interface),
            ISecuredView,
            name)

    exists = registered((interface, IRequest), ITile, name=name)
    if exists:
        msg = u"Unregister tile for '%s' with name '%s'" % (
            str(interface), name)
        logger.debug(msg)
        unregister((interface, IRequest), ITile, name=name)

    registry.registerAdapter(tile, [interface, IRequest], ITile, name,
                             event=False)


class tile(object):
    """Decorator to register classes and functions as tiles.
    """

    def __init__(self, name, path=None, attribute='render',
                 interface=Interface, permission='view',
                 strict=True, _level=2):
        """ see ``registerTile`` for details on the other parameters.
        """
        self.name = name
        if path and not (':' in path or os.path.isabs(path)):
            path = '%s:%s' % (caller_package(_level).__name__, path)
        self.path = path
        self.attribute = attribute
        self.interface = interface
        self.permission = permission
        self.strict = strict

    def __call__(self, ob):
        registerTile(self.name,
                     path=self.path,
                     attribute=self.attribute,
                     interface=self.interface,
                     class_=ob,
                     permission=self.permission,
                     strict=self.strict)
        return ob
