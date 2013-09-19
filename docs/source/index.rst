Teleport
========

.. currentmodule:: teleport

To install, run:

.. code:: bash

    pip install teleport

Teleport's primary object is the *serializer*. A serializer corresponds to a
certain data type and lets the user convert values of this type between their
two representations: the *JSON form* and the *native form*. In order to do
this, a serializer must provide a :meth:`to_json` and a :meth:`from_json`
method.

The *JSON form* represents a valid JSON string, however, for convenience, our
implementation uses an intermediate format, namely the format expectd by
:meth:`json.dumps` from the Python standard library. It is limited to
dictionaries, lists, numbers, booleans, strings and ``None``.

Internally, your application will use the *native form*. It can be as rich as
you want, however, for the most basic types, it happens to be the same as the
JSON form. Even when there is nothing to convert, the serializer is useful
as a way of validating input.

Here is a simple serializer::

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
            required("level", Integer, "0-100")
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

Custom Types With Parameters
----------------------------

Both primitive and wrapper types can also be parametrized, which means that their
serializers will have to be instantiated with parameters and that their JSON form
will have an additional attribute *param*.

Take a look at the source code of :class:`Array` for an example of a primitive
parametrized type, and :class:`OrderedMap` for an example of a wrapper
parametrized type.

Extending Teleport
------------------

The types we created above will mostly work, however, if you expect to deserialize
their schema from JSON, you will be faced with an error::

    >>> Schema.from_json({"type": "Player"})
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "teleport.py", line 178, in from_json
        raise UnknownTypeValidationError("Unknown type", t)
    teleport.UnknownTypeValidationError: Unknown type: 'Player'

In order for :class:`Schema` to become aware of your custom types, you need to
extend Teleport. To do so, create an empty module in your Python application,
say :mod:`cards.teleport`.

.. code:: python

    from teleport import standard_types

    def getter(name):
        if name == "Suit":
            return Suit
        raise KeyError()

    class Suit(BasicWrapper):
        schema = String

        @staticmethod
        def assemble(datum):
            if datum not in ["hearts", "spades", "clubs", "diamonds"]:
                raise ValidationError("Invalid Suit", datum)
            return datum

    globals().extend(standard_types(getter))

:func:`~teleport.standard_types` will inject your custom models into Teleport
via the *getter* parameter. The return value is a dict of freshly recreated 
Teleport serializers. Now, instead of doing::

    from teleport import *

you do::

    from cards.teleport import *

Note that by default, Teleport will use the class name as the name of the
serializer. To override that behavior, give the class a :attr:`type_name`
attribute.

Built-In Serializers
--------------------

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
