Teleport
========

Teleport is a JSON-based extendable system for cross-language serialization
and validation. Teleport is not a serialization *layer*, it is meant to
integrate with a language's type system. Using Teleport for a non-trivial
project involves defining data types. In object-oriented languages, this
involves augmenting your classes to make them serializable.

The real power of Teleport comes from the fact that once a data type is
defined, it can be referenced by name in other data type definitions.

The canonical implementation of Teleport is written in Python.

.. glossary::

    Serializer

        An object that defines a serialization and deserialization function.
        The output of a model's deserialization function must be of the same
        form as the input of its serialization function. Likewise, the input
        of its deserialization function must be of the same form as the output
        of its serialization function. Together, these functions define the
        *native form* as well as the *JSON form* of the data.

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

Teleport provides 8 built-in types. Each implementation must provide 8
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

A schema is always a JSON object, it must always have a *type* attribute. An
array schema also requires an *items* attribute, which will be a schema that
describes every item in the matched array. A struct schema requires a *fields*
attribute, which will be an array of objects describing each property of the
data.

Below is the grammar for a JSON schema:

.. _schema-grammar:

.. productionlist:: schema
    schema: `simple_schema` | `array_schema` | `struct_schema`
    simple_type: '"integer"' | '"float"' | '"string"' | '"boolean"' | '"binary"' |
               : '"json"' | '"schema"'
    simple_schema: '{' '"type"' ':' `simple_type` '}'
    array_schema: '{' '"type"' ':' '"array"' ',' '"items"' ':' `schema` '}'
    struct_schema: '{' '"type"' ':' '"struct"' ',' '"fields"' ':' '[' `fields` ']' '}'
    fields: `field` | `field` ',' `fields`
    field: '{' '"name"'   ':' `string` ','
         :     '"schema"' ':' `schema` '}'

.. note::

    An struct schema cannot define two fields with the same name. Trying to
    deserialize such a schema must result in a validation error.

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
                    "schema": {"type": "string"}
                }
            ]
        }
    }

Implementation Notes
--------------------

While parsing the schema :ref:`grammar <schema-grammar>` is entirely up to the
implementations, it should be noted that the structure of a JSON schema can be
validated by a meta-schema. This is how the canonical Python implementation
works.

For example, *fields* can be described as follows:

.. code:: json

    {
        "type": "array",
        "items": {
            "type": "object",
            "fields": [
                {
                    "name": "name",
                    "schema": {"type": "string"}
                },
                {
                    "name": "schema",
                    "schema": {"type": "schema"}
                }
            ]
        }
    }

