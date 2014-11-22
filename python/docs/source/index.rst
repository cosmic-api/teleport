Python Interface
================

.. currentmodule:: teleport.draft00

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

The purpose of the :func:`t` function is to map *type definitions* to *value
spaces* (in this implementation, instances of :class:`Type`). Conveniently,
every type definition is a JSON value and a value space is the set of all JSON
values that belong to a type instance. Defining everything in terms of JSON
allows us to have a common test suite for all implementations of Teleport.

Type-Checking
-------------

To check if a JSON value is of a certain type, we use the
:meth:`~Type.contains` method:

.. code-block:: python

    >>> t("DateTime").contains(u"2015-04-05T14:30")
    True
    >>> t("DateTime").contains(u"2007-04-05T14:30 DROP TABLE users;")
    False

Both the the :func:`t` function and the :meth:`~Type.contains` method accepts
*JSON values* as input. Teleport uses the same format to represent JSON
as the :mod:`json` module in the Python standard library. Therefore, to
type-check a JSON string, you could do this:

.. code-block:: python

    >>> import json
    >>> t("Float").contains(json.loads("3.14159"))
    True

Serialization
-------------

This implementation provides serialization by extending each type with two
methods: :meth:`from_json` and :meth:`to_json`:

.. code-block:: python

    >>> t("DateTime").from_json(u"2015-04-05T14:30")
    datetime.datetime(2015, 4, 5, 14, 30)
    >>> t("String").from_json(u"2015-04-05T14:30")
    u"2015-04-05T14:30"

.. admonition:: Implementation notes

    Serialization is not mentioned in the Teleport spec because it cannot be
    defined in a language-agnostic way. The upside to this is that implementations
    have the freedom to define serialization logic that fits their programming
    language perfectly. The downside is that this functionality cannot be tested by
    the common test suite.

Concrete and Generic Types
--------------------------

Teleport defines two kinds of types: *concrete* and *generic*.

The JSON definition of a concrete type is its name as a string. For example,
the definition of the Boolean type is :data:`"Boolean"`. When you plug that
definition into :func:`t`, you get an instance of the Boolean type:

.. code-block:: python

    >>> t("Boolean")
    <teleport.draft00.BooleanType at 0x7f56c5183b90>

A generic type's definition encodes an additional piece of data, a parameter
which will be used by :func:`t` to create a type instance. For example, the
built-in Array type needs a parameter which represents the type of its
every element:

.. code-block:: python

    >>> t({"Array": "Boolean"})
    <teleport.draft00.ArrayType at 0x7f56c5194110>

Built-in Types
--------------

The Teleport specification defines ten types: 7 concrete and 3 generic.

Integer
^^^^^^^

Uses instances of :class:`int` and :class:`long` in both the JSON form and the
native form.

.. code-block:: python

    >>> t("Integer").contains(1)
    True
    >>> t("Integer").contains(1L)
    True

Float
^^^^^

Uses instances of :class:`float` in both the JSON form and the native form.

.. code-block:: python

    >>> t("Float").contains(1.0)
    True
    >>> t("Float").contains(1e2)
    True

String
^^^^^^

Uses instances of :class:`unicode` and ASCII strings of type :class:`str` in
both the JSON form and the native form.

.. code-block:: python

    >>> t("String").contains(u"hello world")
    True
    >>> t("String").contains("hello world")
    True
    >>> t("String").contains("hello" + chr(225))
    False

Boolean
^^^^^^^

Uses instances of :class:`boolean` in both the JSON form and the native form.

.. code-block:: python

    >>> t("Boolean").contains(True)
    True

DateTime
^^^^^^^^

The `ISO 8601 <http://www.iso.org/iso/home/standards/iso8601.htm>`_ standard
is used to represent datetime objects in JSON form. In the native form,
instances of :class:`datetime` from the Python standard library are used.

.. code-block:: python

    >>> t("DateTime").contains("2007-04-05T14:30")
    True
    >>> t("DateTime").from_json(u"2015-04-05T14:30")
    datetime.datetime(2015, 4, 5, 14, 30)
    >>> t("String").from_json(u"2015-04-05T14:30")
    u"2015-04-05T14:30"

JSON
^^^^

A wildcard that consists of all JSON values, that is, all values accepted by
the :mod:`json` module from the Python standard library.

.. code-block:: python

    >>> t("JSON").contains([None, 1, "xyz"])
    True

Schema
^^^^^^

This is a very special type. Its value space is the set of all possible inputs
for :func:`t`, all possible type definitions. The Schema type enables dynamic
typing, tagged unions and other high-level possibilities.

.. code-block:: python

    >>> t("Schema").contains("Integer")
    True

Array
^^^^^

Array is a generic type whose parameter is a type definition. This parameter
specifies the type of every element in the array. Uses instances of
:class:`list` in both the JSON form and the native form.

.. code-block:: python

    >>> t({"Array": "Integer"}).contains([1, 2, 3])
    True
    >>> t({"Array": "Integer"}).contains([1, 2, 3.0])
    False

Map
^^^

Similar to the Array type, but using JSON objects in the JSON form and
instances of :class:`dict` in the native form.

.. code-block:: python

    >>> t({"Map": "Float"}).contains({"x": 0.12, "y": 0.87})
    True
    >>> t({"Map": "Integer"}).contains({"a": 1, "b": True})
    False

Struct
^^^^^^

The Struct type uses instances of :class:`dict` for both the JSON and native
form. It is a generic type and its parameter is a JSON object with two members:
*required* and *optional*. Both are of type ``t({"Map": "Schema"})``:

.. code-block:: python

    >>> TODO = t({"Struct": {
    ...            "required": {"task": "String"},
    ...            "optional": {"priority": "Integer",
    ...                         "deadline": "DateTime"}}})

With this type instance, you can validate JSON objects like these:

.. code-block:: python

    >>> TODO.contains({"task": "Return videotapes"})
    True
    >>> TODO.contains({"task": "Return videotapes",
    ...                "deadline": "2015-04-05T14:30"})
    True

Of course, you cannot be missing a required field and each field's schema must
be respected:

.. code-block:: python

    >>> TODO.contains({})
    False
    >>> TODO.contains({"task": 1})
    False

Like Array and Map, Struct performs recursive serialization:

.. code-block:: python

    >>> TODO.from_json({"task": "Return videotapes",
    ...                 "deadline": "2015-04-05T14:30"})
    {u'deadline': datetime.datetime(2015, 4, 5, 14, 30),
     u'task': u'Return videotapes'}


API
---

.. autoclass:: Type
   :members:
   :undoc-members:

Exceptions
----------

.. autoclass:: Undefined
   :members:

