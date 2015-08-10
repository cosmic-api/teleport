:orphan:

Python Interface
================

Teleport's `tiny specification <http://teleport-json.org/spec/latest/>`_
operates entirely on JSON values and mathematical sets, making it
language-agnostic and allowing for a common test suite for all implementations.

This Python library is the first and probably best implementation of Teleport.
Apart from type-checking in conformance with the specification, it implements
serialization as well as a convenient interface for creating new types.

At a Glance
-----------

.. code-block:: bash

    pip install teleport

.. code-block:: python

    >>> from teleport import t
    >>> TODO = t({"Struct": {
    ...            "required": {"task": "String"},
    ...            "optional": {"priority": "Integer",
    ...                         "deadline": "DateTime"}}})
    >>> TODO.check({"task": "Return videotapes"})
    True
    >>> TODO.from_json({"task": "Return videotapes",
    ...                 "deadline": "2015-04-05T14:30:00Z"})
    {'deadline': datetime.datetime(2015, 4, 5, 14, 30, tzinfo=<UTC>),
     'task': u'Return videotapes'}

Contents
--------

.. toctree::
    :maxdepth: 2

    guide
    types
    extending

Reference
---------

.. toctree::
   :maxdepth: 2

   api/type
   api/typemap
   api/errors

Design Notes
------------

These notes explain some of the design decisions of the Teleport specification.
They are here to be refuted and rewised, through the project's `mailing list <https://groups.google.com/forum/#!forum/teleport-json>`_.

.. toctree::
   :maxdepth: 1

   design/principles
   design/json
   design/numbers
   design/datetime

History
-------

Teleport was started in May 2013 and developed as part of `Cosmic <http://www.cosmic-api.com>`_,
little-known web API library by yours truly. It was rewritted from scratch in
November 2014 based on a new and improved specification. With enough eyes and
some helping hands, we should see version 1.0 soon.

.. toctree::
   :maxdepth: 2

   changelog

Contributing
------------

Teleport is a one-man operation with a big scope. The `GitHub repository <http://github.com/cosmic-api/teleport>`_
is kept in good order to welcome all kinds of patches:

* Improvements to the specification (see also: the `mailing list <https://groups.google.com/forum/#!forum/teleport-json>`_)
* Interesting recipes for the :mod:`teleport.examples` module
* Difficult test cases for the language-agnostic test suite
* Tweaks, fixes, aggressive refactorings
* Removing immature humor from the documentation

If you are interested in building web APIs with Teleport, take a look at
`Cosmic <http://www.cosmic-api.com/>`_, a project by the same author. It will
be updated soon with the new Teleport implementation and will become the best
showcase for Teleport.
