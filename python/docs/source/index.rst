Python Interface
================

.. currentmodule:: teleport

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
type-check a JSON-encoded string, you could do this:

.. code-block:: python

    >>> import json
    >>> t("Float").contains(json.loads("3.14159"))
    True

Serialization
-------------

This implementation provides serialization by extending each type with two
methods: :meth:`from_json` and :meth:`to_json`:

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
    >>> t("DateTime").from_json("2015-04-05T14:30")
    datetime.datetime(2015, 4, 5, 14, 30)
    >>> t("DateTime").to_json(datetime.datetime(2015, 4, 5, 14, 30))
    "2015-04-05T14:30"

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


Custom Types
------------

Teleport's specification does not define the totality of the :func:`t`
function, just provides some instances of its inputs and outputs. Any
implementation is allowed to extend it with new instances, inventing new
concrete types, new generic types or other higher-level constructs.

This implementation provides a convenient interface for extending Teleport with
new concrete and generic types. You can see how it works by reading through
the following recipes, but first, in order to keep the global namespace clean,
make your own personal instance of the :func:`t` function:

.. code-block:: python

    from teleport import Teleport, ConcreteType, GenericType

    t = Teleport()

Save this in your project's package, say, in ``types.py``. To use your extended
version of Teleport, simply import your version of :data:`t`:

.. code-block:: python

    from jsonapp.types import t

Recipe: Color
^^^^^^^^^^^^^

Let's add a concrete type that matches all hex-encoded colors. Use the
:meth:`~teleport.Teleport.register` decorator to add a new type to your
:data:`t` instance:

.. code-block:: python

    @t.register("Color")
    class ColorType(ConcreteType):

        def contains(self, value):
            if not t("String").contains(value):
                return False

            return re.compile('^#[0-9a-f]{6}$').match(value) is not None

Once we have called :meth:`~teleport.Teleport.register`, we can use the new
type as a first-class citizen:

.. code-block:: python

    >>> t("Color").contains('#ffffff')
    True
    >>> t("Color").contains('yellow')
    False
    >>> t({"Array": "Color"}).contains(['#ffffff', '#000000']))
    True

If you don't provide your own :meth:`from_json` and :meth:`to_json`
implementations, the default implementation assumes that the native form is
the same as the JSON form:

.. code-block:: python

    >>> t("Color").from_json('#ffffff')
    "#ffffff"

If your purpose for defining custom types is primarily type-checking, then you
can forget about those methods altogether, they don't need to be extended in
order to work.

Recipe: PythonObject
^^^^^^^^^^^^^^^^^^^^

The :mod:`pickle` module from Python's standard library provides generic
serialization of Python objects. Even though :mod:`pickle` makes the author
nervous, we will use it to give Teleport the same power:

.. code-block:: python

    import pickle

    @t.register("PythonObject")
    class PythonObjectType(ConcreteType):

        def from_json(self, json_value):
            if not t("String").contains(json_value):
                raise Undefined("PythonObject must be a string")
            return pickle.loads(json_value)

        def to_json(self, native_value):
            return pickle.dumps(native_value)

Note that if we implement :meth:`from_json`, implementing :meth:`contains` is
not necessary, as long as your :meth:`from_json` implementation behaves
correctly by throwing :exc:`Undefined`.

Now we can use it to serialize most Python objects:

.. code-block:: python

    >>> t("PythonObject").to_json(set([1, 2]))
    'c__builtin__\nset\np0\n((lp1\nI1\naI2\natp2\nRp3\n.'

.. warning::

    Pickle is unsafe with untrusted data. You probably shouldn't actually use
    this type.

Recipe: Nullable
^^^^^^^^^^^^^^^^

Teleport does not encourage using null unless there is a good reason for it.
One good reason is an existing format using null. Either way, the following
generic type is a good way to introduce it:

.. code-block:: python

    @t.register("Nullable")
    class NullableType(GenericType):

        def process_param(self, param):
            self.child = self.t(param)

        def from_json(self, value):
            if value is None:
                return None
            return self.child.from_json(value)

        def to_json(self, value):
            if value is None:
                return None
            return self.child.to_json(value)

Now you can define weird types like this:

.. code-block:: python

    >>> s = t({"Array": {"Nullable": "String"}})
    >>> s.contains(["sparse", None, "arrays", None, None, None, "what"])
    True

More realistically, you might use it to deal with JSON objects with null
values. The reason this type is not in Teleport core is to discourage us from
creating these monsters:

.. code-block:: python

    >>> s = t({"Struct": {
    ...          "required": {"id": "Integer"},
    ...          "optional": {"name": {"Nullable": "String"},
    ...                       "age":  {"Nullable": "Integer"}}}})

Even though they may be useful for reading objects like these:

.. code-block:: python

    >>> s.contains({"id": 1, "name": "Jake", "age": 28})
    True
    >>> s.contains({"id": 1, "name": None, "age": 12})
    True
    >>> s.contains({"id": 1, "age": None})
    True

API
---

.. autoclass:: Type
   :members:
   :undoc-members:

.. autoclass:: Teleport
   :members:
   :undoc-members:

.. autoclass:: Undefined
   :members:

