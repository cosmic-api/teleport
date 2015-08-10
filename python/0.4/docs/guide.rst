Guide
=====

Installation
------------

Teleport is available on `PyPI <https://pypi.python.org/pypi/teleport>`_, and,
if you have pip, you can install it like so:

.. code-block:: bash

    pip install teleport

Introduction
------------

Teleport is a JSON type system. Its language-agnostic specification asks only
for one function to be exported:

.. code-block:: python

    >>> from teleport import t

The purpose of the :func:`t() <teleport.TypeMap.__call__>` function is to map
*type definitions* to *value spaces* (in this implementation, instances of
:class:`~teleport.Type`). Conveniently, every type definition is a JSON value
and a value space is the set of all JSON values that belong to a type instance.
Defining everything in terms of JSON allows us to have a common test suite for
all implementations of Teleport.

Type-Checking
-------------

To check if a JSON value is of a certain type, we use the :meth:`~Type.check`
method:

.. code-block:: python

    >>> t("DateTime").check(u"2015-04-05T14:30")
    True
    >>> t("DateTime").check(u"2007-04-05T14:30 DROP TABLE users;")
    False

Both the the :func:`t() <teleport.TypeMap.__call__>` function and the
:meth:`~teleport.Type.check` method accepts *JSON values* as input. Teleport
uses the same format to represent JSON as the :mod:`json` module in the Python
standard library. Therefore, to type-check a JSON-encoded string, you could do
this:

.. code-block:: python

    >>> import json
    >>> t("Decimal").check(json.loads("3.14159"))
    True

Serialization
-------------

This implementation provides serialization by extending each type with two
methods: :meth:`~teleport.Type.from_json` and :meth:`~teleport.Type.to_json`:

.. code-block:: python

    >>> t("DateTime").from_json("2015-04-05T14:30")
    datetime.datetime(2015, 4, 5, 14, 30)
    >>> t("DateTime").to_json(datetime.datetime(2015, 4, 5, 14, 30))
    "2015-04-05T14:30"

For container types they work recursively:

.. code-block:: python

    >>> t({"Array": "DateTime"}).from_json(["2015-04-05T14:30"])
    [datetime.datetime(2015, 4, 5, 14, 30)]

.. admonition:: Implementation notes

    Serialization is not mentioned in the Teleport spec because it cannot be
    defined in a language-agnostic way. Implementations have the freedom to
    define serialization logic that best fits their programming language, but
    this functionality cannot be tested by the common test suite.

Concrete and Generic Types
--------------------------

Teleport defines two kinds of types: *concrete* and *generic*.

The JSON definition of a concrete type is a string containing its name. For
example, the definition of the Boolean type is :data:`"Boolean"`. When you plug
that definition into :func:`t`, you get an instance of the Boolean type:

.. code-block:: python

    >>> t("Boolean")
    <teleport.BooleanType at 0x7f56c5183b90>

A generic type's definition encodes an additional piece of data, a parameter
which will be used by :func:`t` to create a type instance. For example, the
built-in Array type needs a parameter:

.. code-block:: python

    >>> t({"Array": "Boolean"})
    <teleport.ArrayType at 0x7f56c5194110>

.. seealso::

    For a list of core types from the Teleport specification, see :doc:`types`.
    To learn how to create custom types, see the :doc:`extending` section.
