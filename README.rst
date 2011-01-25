=================================
Tiles for use in repoze.bfg Views
=================================

Enables repoze.bfg to render a website constisting of flexible tiles. 

A tile is a piece of web application, i.e. a form, a navigation, etc. 

Those HTML-Snippets looked up dynamically using the ZCA.

Splitting your application in such small and logic application parts makes it
easy to re-use this application, simplifies application ajaxification and
the use of same application parts in different manners.

Contributors
============

- Jens Klein <jens@bluedynamics.com>

- Robert Niederreiter <rnix@squarewave.at>


Changelog
=========

1.1
---

- fix the nasty caller_packages level.
  (jensens, 2010-01-04) 

- Tiles can now consume Forbidden and return emtpy string, default still
  raises exception.
  (jensens, 2009-12-31) 

- Upgrade to make it work with repoze.bfg 1.2 
  (jensens, 2009-12-30) 

1.0
---

- Make it work

API-Documentation via Doctests
==============================

(To be made better in future)
