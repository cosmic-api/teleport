Introduction
============

.. note::

     If you're looking to dive right in, check out the `Python docs
     </docs/teleport/python/>`_.

Teleport is a JSON-based extendable system for cross-language serialization
and validation. Teleport is not a serialization *layer*, it is meant to
integrate with a language's type system. Teleport provides 9 built-in data
types to get you started, however, using Teleport for a non-trivial project
means defining data types of your own. In object-oriented languages, this
involves augmenting your classes to make them serializable.

Once registered with Teleport, a custom data type will become a first-class
citizen within your application. Defining an array of integers is just as easy
as defining an array of widgets, provided that you made the Widget class
serializeable.

Such definitions (like "array of widgets") are also serializable. This feature
is crucial in allowing `Cosmic <http://www.cosmic-api.com/>`_ clients to share
a deeper understanding of each other.

The canonical implementation of Teleport is written in Python.

Teleport Spec
=============

.. glossary::

    Serializer

        An object that defines a serialization and deserialization function.
        The output of the deserialization function must be of the same form as
        the input of the serialization function. Likewise, the input of the
        deserialization function must be of the same form as the output of the
        serialization function. Together, these functions define the *native
        form* as well as the *JSON form* of the data.

        Serializers may take parameters. For example, an array serializer
        needs to know what type of items the array is expected to contain.

    Native form

        Data in its rich internal representation. For most built-in types,
        this data will consist of language primitives. In object-oriented
        languages, the native form of user-defined types will often take the
        form of class instances.

    JSON form

        Data in its JSON represenation. There are many ways to represent the
        same data in JSON. This representation must be reasonably readable
        and, most importantly, unambiguous.

    Deserialization

        Turning data as provided by the JSON parser into its native form.
        Validation is always performed during this step.

    Serialization

        Turning data in its native form into the format expected by the JSON
        serializer. Validation is *not* performed during this step.


Built-In Types
--------------

Teleport provides 9 built-in types. Each implementation must provide 9
corresponding serializers.

The native form of the built-in types is implementation-dependent and will be
defined in language-specific documentation. The serialized form and the
validation logic, however, is identical across all implementations. Below is a
list of all built-in models and their validation logic.

``integer``
    Must be expressed as a JSON number. If the number has a decimal, the
    fractional part must be 0.

``float``
    Must be expressed as a JSON number. Implementations should support double-precision.

``string``
    Must be expressed as a JSON string. Encoding must be UTF-8. Unicode errors
    must be dealt with strictly by throwing a validation error.

``boolean``
    Must be expressed as a JSON boolean.

``binary``
    Must be expressed as a JSON string containing Base64 encoded binary data.
    Base64 errors must result in a validation error.

``json``
    Can be any JSON value. No validation is performed during deserialization.
    Depending on the implementation, it may be useful to wrap the JSON in a
    different object, so that a ``null`` JSON value won't cause ambiguity.

``array`` (parametrized by *items*)
    Must be expressed as a JSON array. The implementation must deserialize
    each of its items against the *items* serializer. If an item
    deserialization fails with a validation error, the array deserialization
    must fail likewise. The native form of an array must be an ordered
    sequence of native values, in the same order as they appear in the JSON
    form. If the array was empty, an empty sequence must be returned.

``struct`` (parametrized by *fields*)
    Must be expressed as a JSON object. If the object has a key that is
    different from every field name in *fields*, a validation error must be
    thrown. For every key-value pair in the object, the value must be
    normalized against the *schema* of the corresponding field in *fields*.
    The native form of the object must be an associative array containing all
    key-value pairs from the original object with native values replacing the
    JSON values.

``schema``
    See the following section.


Schemas
-------

.. glossary::

    Schema

        The JSON form of a :term:`serializer`.

One of the unique design requirements of Teleport is being able to pass
serializers over the wire by means of a JSON schema.

A schema is always a JSON object, it must always have a *type* property.
All built-in types except for ``array`` and ``struct`` contain no other
properties.

An ``array`` schema must contain a property *items*, whose value must be a
schema that describes every item in the array.

A ``struct`` schema must contain a property *fields*, which must be an array
of field objects. Each field object must contain 3 properties: *name*,
*schema* and *required*. *Name* must be a string, there cannot be two field
objects in a ``struct`` schema with the same name. *Schema* must be a schema
that describes the value matched by the *name*. *Required* must be a boolean
that specifies whether omitting the item will cause a validation error or not.

To validate ``[{"name": "Rose"}, {"name": "Lily"}]``, you could use the
following schema:

.. code:: json

    {
        "type": "array",
        "items": {
            "type": "struct",
            "fields": [
                {
                    "name": "name",
                    "schema": {"type": "string"},
                    "required": true
                }
            ]
        }
    }

Implementation Notes
--------------------

How to validate schema parameters is up to the implementation. However, it
should be noted that these parameters can be described as Teleport schemas
themselves. For example, *fields* can be described as follows:

.. code:: json

    {
        "type": "array",
        "items": {
            "type": "struct",
            "fields": [
                {
                    "name": "name",
                    "schema": {"type": "string"},
                    "required": true
                },
                {
                    "name": "schema",
                    "schema": {"type": "schema"},
                    "required": true
                },
                {
                    "name": "required",
                    "schema": {"type": "boolean"},
                    "required": true
                }
            ]
        }
    }

Note that after using the above schema the implementation still needs to make
sure there are no duplicate names.

