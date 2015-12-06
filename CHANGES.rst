
Changelog
=========

1.0 (unreleased)
----------------

- ``tile`` decorator uses ``venusian`` to defer tile registration now.

- Accept ``name`` as keyword instead of positional argument in
  ``register_tile`` and ``tile`` decorator.
  [rnix, 2015-11-06]

- ``registerTile`` has been renamed to ``register_tile``.
  [rnix, 2015-11-06]

- Update to pyramid 1.5
  [rnix, 2015-11-02]

- Remove useless test case due to this change.
  https://github.com/Pylons/pyramid/commit/4b552e539a1725356b9982261b73fd88de7d59a1#diff-bcda6948340ab38542fe18fd2365ac70R144
  [rnix, 2015-11-02]


0.9.2
-----

- using and depending now on zope.exceptions to format tracebacks with
  supplements.
  [jensens, 2012-06-06]

- improved visibility of tracebacks, they appear now in the error log.
  even if an expression like ```tal:replace="structure tile('editform')"```
  ate it, the traceback is logged. traceback supplements are rendered.
  [jensens, 2012-06-05]

- removed superfluos try except
  [jensens, 2012-06-05]

- fixed dependencies for integrated tests
  [jensens, 2012-06-05]


0.9.1
-----

- Tiles can be overwritten.
  [rnix, 2012-05-22]

- Use ``zope.interface.implementer`` instead of ``zope.interface.implements``.
  [rnix, 2012-05-18]


0.9
---

- Fit for pyramid 1.1 + 1.2
  [rnix, 2011-09-08]

- Documentation
  [rnix, 2011-09-08]

- Make it work
  [jensens, rnix, et. al]
