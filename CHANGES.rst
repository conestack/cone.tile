
Changelog
=========

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
