Teleport
========

.. currentmodule:: teleport

A *serializer* is a class that provides a :meth:`serialize` and a
:meth:`deserialize` method. Teleport provides 9 basic serializers and lets you
define your own.

The output of the :meth:`serialize` method and the input of the
:meth:`deserialize` method is in the format of the :mod:`json` module from the
Python standard library. This is the *JSON form* of the data. The *native form*
can be as rich as you want, although for most of the built-in types it will be
the same as the JSON form.

Simple serializers are instantiated with no arguments::

    >>> from teleport import *
    >>> Integer().deserialize(1)
    1

As you can see, the :class:`Integer` serializer doesn't do much. Why do we even
have it as a class? Because it can be used as a parameter for more complex
serializers, such as the :class:`Array`::

    >>> array_of_integers = Array(Integer())
    >>> array_of_integers.deserialize([1, 2, 3, 4, 5])
    [1, 2, 3, 4, 5]
    >>> array_of_integers.deserialize([1, 2, 3, 4, 5.1])
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "teleport.py", line 175, in deserialize
        ret.append(self.items.deserialize(item))
      File "teleport.py", line 62, in deserialize
        raise ValidationError("Invalid integer", datum)
    teleport.ValidationError: Item at [4] Invalid integer: 5.1

``array_of_integers`` is an interesting object. It may be useful to send it
over the wire, and with Teleport it is actually very easy to do. Teleport provides
a special serializer :class:`Schema` for serializing other serializers::

    >>> Schema().serialize(array_of_integers)
    {'type': 'array', 'items': {'type': 'integer'}}

The client that receives this JSON object can then deserialize it::

    >>> Schema().deserialize({'type': 'array', 'items': {'type': 'integer'}})
    <teleport.Array object at 0xb7189d6c>

Another complex serializer is the :class:`Struct`. It is used for dicts with
non-arbitrary keys::

    >>> from teleport import Struct, required, optional
    >>> s = Struct([
    ...     required("name", String()),
    ...     optional("scores", array_of_integers)
    ... ])
    >>> s.deserialize({"name": "Bob"})
    {"name": u"Bob"}
    >>> s.deserialize({"name": "Bob", "scores": [1, 2, 3.1]})
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "teleport.py", line 268, in deserialize
        ret[field] = schema.deserialize(datum[field])
      File "teleport.py", line 196, in deserialize
        ret.append(self.items.deserialize(item))
      File "teleport.py", line 71, in deserialize
        raise ValidationError("Invalid integer", datum)
    teleport.ValidationError: Item at ['scores'][2] Invalid integer: 3.1

Creating Custom Types
---------------------

.. autoclass:: TypeMap

   .. automethod:: middleware

Custom Types With Parameters
----------------------------

The JSON form of a simple type such as integer or suit contains nothing but
the type name::

    >>> Schema().serialize(Integer())
    {'type': 'integer'}
    >>> Schema().serialize(Suit())
    {'type': 'suit'}

But if you look at the JSON form of an array type, you can see that it has a
parameter *items*. It is quite easy to create custom types with parameters,
take a look at the source code of :class:`Array` for a simple example.

Built-In Serializers
--------------------

.. data:: BUILTIN_TYPES

   A dictionary mapping type names to serializer classes. By default, contains
   the following members: 
   ``"integer"`` (:class:`Integer`),
   ``"float"`` (:class:`Float`),
   ``"boolean"`` (:class:`Boolean`),
   ``"string"`` (:class:`String`),
   ``"binary"`` (:class:`Binary`),
   ``"json"`` (:class:`JSON`),
   ``"array"`` (:class:`Array`),
   ``"struct"`` (:class:`Struct`) and
   ``"schema"`` (:class:`Schema`).

.. autoclass:: Integer
   :members:

.. autoclass:: Float
   :members:

.. autoclass:: Boolean
   :members:

.. autoclass:: String
   :members:

.. autoclass:: Binary
   :members:

.. autoclass:: JSON
   :members:

.. autoclass:: Box
   :members:

.. autoclass:: Array

   .. automethod:: serialize
   .. automethod:: deserialize
   .. automethod:: serialize_self
   .. automethod:: deserialize_self

.. autoclass:: Struct

   .. automethod:: serialize
   .. automethod:: deserialize
   .. automethod:: serialize_self
   .. automethod:: deserialize_self

.. autoclass:: Schema

   .. automethod:: serialize
   .. automethod:: deserialize

Exceptions
----------

.. autoclass:: ValidationError
   :members:

.. autoclass:: UnicodeDecodeValidationError

.. autoclass:: UnknownTypeValidationError
