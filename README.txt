Introduction
============
Reflecto is a tool to incorporate part of the file system into a Plone site.
It allows you to browse through a filesystem hierarchy and access the files
in it. Files are represented as simple downloadable object, not as full CMF
or Plone content types.

Requirements
============

* Plone 3.1 or later

* TextIndexNG3 is optional, but needed to index non-text files.


Filename policies
=================

Filenames must be valid Zope ids. In addition, filenames starting with
a dot, or with '@@' are also deemed invalid. Files with names not matching
these criteria will be ignored.

This means that filenames must basically be ASCII characters only, and not
start with ``aq_``, ``@@``, ``.`` or ``_``, not end with ``__`` nor
contain a ``+``.
  
  
More information
================

For new releases please visit the `Reflecto product page`_ on plone.org.

Please report bugs and feature requests in the `Reflecto issue tracker`_.


.. _Reflecto product page: http://plone.org/products/reflecto
.. _Reflecto issue tracker: http://plone.org/products/reflecto/issues
                                                     

Copyright
=========

Reflecto is Copyright 2007 by Jarn AS
Reflecto is Copyright 2008-2009 by Simplon

Reflecto is distributed under the GNU General Public License, version 2. A
copy of the license can be found in GPL.txt in the doc directory.

The chardet Universal Encoding Detector is copyright 2006 by Mark Pilgrim.
Portions of chardet are copyright 1998-2001 Netscape Communications
Corporation.

chardet is distributed under the GNU Lesser General Public License, version
2.1. A copy of the license can be found in LGPL.txt in the doc directory.

The Reflecto character description is copyrighted by Wikipedia contributors
and licensed to the public under the GNU Free Documentation License (GFDL). A
copy of the license can be found in GFDL.txt in the doc directory.


Credits
=======

Funding
    Trolltech_

Design and Development --
    Jarn_
    Simplon_
    Wichert Akkerman, Martijn Pieters

`Universal Encoding Detector`_
    Mark Pilgrim, Netscape Communications Corporation

.. _Trolltech: http://www.trolltech.com/
.. _Jarn: http://www.jarn.com
.. _Simplon: http://www.simplon.biz
.. _Universal Encoding Detector: http://chardet.feedparser.org

