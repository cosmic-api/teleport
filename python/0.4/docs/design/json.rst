Relationship to JSON
--------------------

.. epigraph::

   The fundamental problem addressed by a type theory is to ensure that programs have meaning.

   -- Mark Manasse

Type systems are responsible for mapping meaning to programming constructs.
These constructs could be ethereal mathematical objects or actual bits in your
computer's memory -- what matters is that on one side we have substance and on
the other essense.

The JSON specification does not attach any meanings to the values it defines,
nor does it call them types. It simply defines a set of mathematical objects
and a way to transform them into strings. The task of interpreting JSON values
is performed at the implementation level.

JSON implementations, however, are not concerned with meaning -- they are
concerned with basic serialization. As such, they do the minimum by mapping atomic
types to convenient native counterparts and treating all structured types as
collections of arbitrary objects.

If you look at any real JSON document, however, you will see far more that:
instead of JSON objects you will see Structs and Maps, some strings will stand
out as DateTimes and numbers will give you hints as to their function.

Teleport uses JSON as a foundation and builds a layer on meaning on top of it.
We try to *invent* as little as possible, preferring to instead *discover* it
in existing JSON usage. The depth of meaning provided by Teleport is set by the
design requirements of the software that uses it. If you stick to the core
Teleport types, it will indeed serve as a thin layer, bridging the gap between
unstructured and structured data but going no further. If you choose to extend
Teleport, the depth of meaning will be unlimited, at the cost of reduced
interoperability with other Teleport implementations.

