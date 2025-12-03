Changes
=======

2.0.0 (unreleased)
------------------

- Setup Makefile.
  [lenadax]

- Run tests with pytest.
  [lenadax]


1.2 (2025-10-25)
----------------

- Pin upper versions of dependencies.
  [rnix]

- Setup Makefile.
  [lenadax]

- Run tests with pytest.
  [lenadax]


1.1 (2022-12-05)
----------------

- Release wheel.
  [rnix]


1.0 (2019-11-07)
----------------

- Drop pyramid support < 1.5.
  [rnix, 2019-03-24]

- Python 3 compatibility.
  [rnix, 2019-03-24]

- Do not use ``cgi`` module if replacement module ``html`` available.
  [rnix, 2019-03-24]

- Convert doctests to unittests.
  [rnix, 2019-03-21]

- ``tile`` decorator uses ``venusian`` to defer tile registration now.
  [rnix, 2015-11-06]

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


0.9.6
-----

- Use ``traceback`` module instead of ``zope.exceptions`` to format
  exceptions in ``render_template``.
  [rnix, 2017-10-06]


0.9.5
-----

- Remove ``log_exception`` utility and use registered ``IDebugLogger`` in
  ``cone.tile._api.render_template`` for exception logging.
  [rnix, 2017-03-24]


0.9.4
-----

- Tile registration ``name`` is taken from ``Tile`` subclass if not given
  in ``registerTile`` function and ``tile`` decorator.
  [rnix, 2017-02-17]

- ``name`` is now optional in ``registerTile`` function and ``tile`` decorator.
  [rnix, 2017-02-17]

- Default ``attribute`` is now ``None`` in ``registerTile`` function and
  ``tile`` decorator to ensure considering ``attribute`` from ``Tile`` subclass
  if set.
  [rnix, 2017-02-17]

- ``Tile.name``, ``Tile.path`` and ``Tile.attribute`` can be set on ``Tile``
  subclass directly without being overwritten at tile registration if not
  given.
  [rnix, 2017-02-17]


0.9.3
-----

- Errors caught in ``render_tile`` may contain umlaute. Properly decode error
  string.
  [rnix, 2017-02-13]


0.9.2
-----

- Using and depending now on zope.exceptions to format tracebacks with
  supplements.
  [jensens, 2012-06-06]

- Improved visibility of tracebacks, they appear now in the error log.
  even if an expression like ```tal:replace="structure tile('editform')"```
  ate it, the traceback is logged. traceback supplements are rendered.
  [jensens, 2012-06-05]

- Removed superfluos try except
  [jensens, 2012-06-05]

- Fixed dependencies for integrated tests
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
