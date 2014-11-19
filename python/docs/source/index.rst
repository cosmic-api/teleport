Documentation
=============

.. currentmodule:: teleport.draft00

Installation
------------

Teleport is available on `PyPI <https://pypi.python.org/pypi/teleport>`_, and
if you have pip, you can install it this way:

.. code:: bash

    pip install teleport

Type-Checking
-------------

In Teleport, a type is essentially a set of JSON values. Type-checking is done
via the set membership interface:

.. code:: python

    >>> from teleport import t
    >>> 1 in t("Integer")
    True

So if ``t("Integer")`` is a set, what is :func:`t`? The :func:`t` function
is the very core of Teleport and probably the only import you will need. It is
a function that maps type definitions to type objects.

With the notable exception of Boolean, most types are infinite sets of values
and a fundamental goal of Teleport is to provide a short, portable and
unambiguous representation for every type: the type definition, also known as
*schema*. As evident from above, the JSON string ``"Integer"`` is a valid
type definition.

There are 7 built-in *concrete types*, types like Integer, whose definitions
are JSON strings; there are also 3 built-in *generic types*, types whose
definitions include a parameter:

.. code-block:: python

    >>> [1, 2, 3] in t({"Array": "Integer"})
    True
    >>> [1, 2, 3.0] in t({"Array": "Integer"})
    False

All type definitions are JSON values.

Serialization
-------------

When we talk about serialization, we are talking about mappings between native
Python values and JSON values. You may point out that serialization involves
mapping native values to *strings*, but since the mapping between strings and
JSON values is taken care of by the JSON standard, we can use JSON values as
the lowest-level data representation.

Because we need to be able to serialize as well as deserialize, this is a
two-way mapping, defined by two functions: :meth:`to_json` and
:meth:`from_json`. The argument for :meth:`from_json` and the return value of
:meth:`to_json` must be a JSON

.. code-block:: python

    >>> t("DateTime").from_json(u"2015-04-05T14:30")
    datetime.datetime(2015, 4, 5, 14, 30)
    >>> t("String").from_json(u"2015-04-05T14:30")
    u"2015-04-05T14:30"

The opposite is also true. This is because the

For the purpose of type-checking, a type is nothing but a set of JSON values.
This is not enough for serialization.

this is not enough, there must also be a
mapping between this set and a set of native Python values. This is a two-way
mapping defined for every type as a pair of functions:

Built-In Types
--------------

.. code:: python

    >>> 1 in t("Integer")
    True
    >>> 1.0 in t("Float")
    True
    >>> u"hello world" in t("String")
    True
    >>> True in t("Boolean")
    True
    >>> "2007-04-05T14:30" in t("DateTime")
    True
    >>> [None, 1, "xyz"] in t("JSON")
    True
    >>> "Integer" in t("Schema")
    True

Numeric
-------

Blah blah

String
------

Blah

Exceptions
----------

.. autoclass:: Undefined
   :members:

