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
   api
   notes
   changelog

