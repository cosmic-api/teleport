Built-in Types
--------------

.. seealso::

    To learn how to create custom types, see the :doc:`extending` section.

The Teleport specification defines ten types: 7 concrete and 3 generic.

.. _type-integer:

Integer
^^^^^^^

Uses instances of :class:`int` and :class:`long` in both the JSON form and the
native form.

.. code-block:: python

    >>> t("Integer").contains(1)
    True
    >>> t("Integer").contains(1L)
    True

.. _type-decimal:

Decimal
^^^^^^^

Uses instances of :class:`int`, :class:`long`, :class:`float` and
:class:`~decimal.Decimal` in both the JSON form and the native form.

.. code-block:: python

    >>> t("Decimal").contains(0)
    True
    >>> t("Decimal").contains(1.0)
    True
    >>> t("Decimal").contains(1e2)
    True

.. seealso::

    To read more about floats and decimals, see :ref:`on-numeric-types`. Skip
    ahead to :ref:`decimal-precision` to see how to safely parse precise
    decimal numbers.

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

The `RFC 3339 <http://tools.ietf.org/html/rfc3339>`_ (proposed) standard
is used to represent datetime objects in JSON form. In the native form,
instances of :class:`~datetime.datetime` from the Python standard library are used.

.. code-block:: python

    >>> t("DateTime").contains('2013-10-18T01:58:24.904349Z')
    True
    >>> a = t("DateTime").from_json('2013-10-18T01:58:24.904349Z')
    >>> a
    datetime.datetime(2013, 10, 18, 1, 58, 24, 904349, tzinfo=<UTC>)
    >>> t("DateTime").to_json(a)
    '2013-10-18T01:58:24.904349Z'

.. seealso::

    :ref:`on-datetime-standards` discusses the choice of RFC 3309 over
    ISO 8601.

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

    >>> t({"Map": "Decimal"}).contains({"x": 0.12, "y": 0.87})
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

Of course, you cannot omit a required field and each field's schema must be
respected:

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


