Teleport
========

.. currentmodule:: teleport

To install, run:

.. code:: bash

    pip install teleport

A *serializer* is an object that provides a :meth:`to_json` and a
:meth:`from_json` method. At the moment, Teleport provides 11 built-in
serializers.

The output of the :meth:`to_json` method and the input of the
:meth:`from_json` method is in the format of the :mod:`json` module from the
Python standard library. This is the *JSON form* of the data. The *native
form* can be as rich as you want, although for most of the built-in types
it will be the same as the JSON form.

Here is a basic serializer::

    >>> from teleport import *
    >>> Integer.from_json(1)
    1

**Integer** is a *basic type*, it is represented by the :class:`Integer`
class, which does not need to be instantiated because the type takes no
parameters. **Array** is a *parametrized type*, it is represented by the
:class:`Array` class, which is instantiated with a parameter::

    >>> Array(Integer).from_json([1, 2, 3, 4, 5])
    [1, 2, 3, 4, 5]
    >>> Array(Integer).from_json([1, 2, 3, 4, 5.1])
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "teleport.py", line 349, in from_json
        ret.append(self.param.from_json(item))
      File "teleport.py", line 208, in from_json
        raise ValidationError("Invalid Integer", datum)
    teleport.ValidationError: Item at [4] Invalid Integer: 5.1

``Array(Integer)`` is an interesting object. It may be useful to send it over
the wire, and with Teleport it is actually very easy to do. Teleport provides
a special serializer :class:`Schema` for serializing other serializers::

    >>> Schema.to_json(Array(Integer))
    {'type': 'Array', 'param': {'type': 'Integer'}}

The client that receives this JSON object can then deserialize it::

    >>> Schema.from_json({'type': 'Array', 'param': {'type': 'Integer'}})
    <teleport.Array object at 0xb7189d6c>

Pretty cool, huh? But actually, :class:`Schema` isn't all *that* special. You
can use it just like any other serializer. For instance, here is an array of
schemas::

    >>> Array(Schema).to_json([Integer, Boolean, Float])
    [{'type': 'Integer'}, {'type': 'Boolean'}, {'type': 'Float'}]

Another parametrized type is the :class:`Struct`. It is used for dicts with
non-arbitrary keys::

    >>> from teleport import Struct, required, optional
    >>> s = Struct([
    ...     required("name", String),
    ...     optional("scores", Array(Integer))
    ... ])
    >>> s.from_json({"name": "Bob"})
    {"name": u"Bob"}
    >>> s.from_json({"name": "Bob", "scores": [1, 2, 3.1]})
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "teleport.py", line 406, in from_json
        ret[field] = schema.from_json(datum[field])
      File "teleport.py", line 349, in from_json
        ret.append(self.param.from_json(item))
      File "teleport.py", line 208, in from_json
        raise ValidationError("Invalid Integer", datum)
    teleport.ValidationError: Item at ['scores'][2] Invalid Integer: 3.1

Creating Custom Types
---------------------

To create a custom type, define a serializer class::

    class YesNoMaybe(object):

        @staticmethod
        def from_json(datum):
            if datum not in [True, False, None]:
                raise ValidationError("Invalid YesNoMaybe", datum)
            return datum

        @staticmethod
        def to_json(datum):
            return datum

:class:`YesNoMaybe` is a *primitive serializer* as it defines functions to
convert data directly to and from JSON. Another option is a *wrapper
serializer*, which relies on an internal serializer for dealing with JSON and
builds on top of it by defining :meth:`assemble` and :meth:`disassemble`
methods.

The :meth:`assemble` method may be used to perform additional validation that
the internal serializer doesn't take care of::

    class Suit(BasicWrapper):
        schema = String

        @staticmethod
        def assemble(datum):
            if datum not in ["hearts", "spades", "clubs", "diamonds"]:
                raise ValidationError("Invalid Suit", datum)
            return datum

Note that the :class:`BasicWrapper` mixin defines the :meth:`to_json` and
:meth:`from_json` functions for you::

    >>> Suit.from_json("hearts")
    "hearts"
    >>> Suit.from_json("heart")
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "teleport.py", line 406, in from_json
        ret[field] = schema.from_json(datum[field])
      File "teleport.py", line 349, in from_json
        ret.append(self.param.from_json(item))
    teleport.ValidationError: Invalid Suit: "heart"

When the native form of the data type is a class instance,
:class:`BasicWrapper` can be used to teach the class to serialize itself::

    class Player(BasicWrapper):
        schema = Struct([
            required("name", String),
            # Note how struct fields can accept an optional doc parameter
            required("level", Integer, "From zero (0) to hero (100)")
        ])

        @staticmethod
        def assemble(datum):
            return Player(**datum)

        @staticmethod
        def disassemble(player):
            return {
                "name": player.name,
                "level": player.level
            }

Before integrating Teleport, :class:`Player` was just a class in your
application, but now you can use it to build schemas like ``Array(Player)``.

Custom Types With Parameters
----------------------------

Both primitive and wrapper types can also be parametrized, which means that their
serializers will have to be instantiated with parameters and that their JSON form
will have an additional attribute *param*.

Take a look at the source code of :class:`Array` for an example of a primitive
parametrized type, and :class:`OrderedMap` for an example of a wrapper
parametrized type.

Informing Teleport Of Your Custom Types
---------------------------------------

.. autoclass:: TypeMap
   :members:

Built-In Serializers
--------------------

.. data:: BUILTIN_TYPES

   A dictionary mapping type names to serializer classes. By default, contains
   the following members: 
   ``"Integer"`` (:class:`Integer`),
   ``"Float"`` (:class:`Float`),
   ``"Boolean"`` (:class:`Boolean`),
   ``"String"`` (:class:`String`),
   ``"Binary"`` (:class:`Binary`),
   ``"JSON"`` (:class:`JSON`),
   ``"Array"`` (:class:`Array`),
   ``"Map"`` (:class:`Map`),
   ``"OrderedMap"`` (:class:`OrderedMap`),
   ``"Struct"`` (:class:`Struct`) and
   ``"Schema"`` (:class:`Schema`).

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
   :members:

.. autoclass:: Map
   :members:

.. autoclass:: OrderedMap
   :members:

.. autoclass:: Struct
   :members:

.. autoclass:: Schema
   :members:


Exceptions
----------

.. autoclass:: ValidationError
   :members:

.. autoclass:: UnicodeDecodeValidationError

.. autoclass:: UnknownTypeValidationError
