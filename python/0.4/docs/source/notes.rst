Design Notes
============

.. currentmodule:: teleport

Design Principles
-----------------

.. epigraph::

    This advice is corrosive. It warps the minds of youth.

    -- Nickieben Bourbaki on `Worse Is Better <http://dreamsongs.com/RiseOfWorseIsBetter.html>`_

This project is dedicated to doing *The Right Thing* from the start. Premature
compromises start avalanches of complexity. The design of Teleport is guided by
keeping clearly defined roles for the specification, the implementations and
the test suite.

Teleport's formal specification aims to be a perfect mathematical snowflake.
To make the specification aware of its implementation is to compromise its
simplicity, which is why Teleport's specification is kept blissfully unaware,
floating in the realm of infinite sets and not concerning itself with mortal
problems.

Implementations of Teleport, on the other hand, are encouraged to compromise by
breaking the specification to meet their requirements -- it's cool, no hard
feelings. This doesn't mean they won't be judged, however -- by the test suite,
whose job is to maintain correctness and guide interoperability.

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

What Is a Type?
---------------

A Teleport type is created by providing two things:

1. A set of all JSON values that can be the type's members
2. A way to interpret a JSON value according to the type

This is the implementation-agnostic definition of a type. When looking at the
implementation, these points roughly correspond to :meth:`Type.check` and
:meth:`Type.from_json`.

Teleport comes with 10 built-in types. Two of them, String and Boolean, don't
add any meaning to their JSON conterparts, but are nonetheless useful for
composability. The other 8 are intepretations of JSON usage.

.. _on-numeric-types:

On Numeric Types
----------------

.. seealso::

    The two built-in numeric types: :ref:`type-integer` and :ref:`type-decimal`.


Interpreting JSON Numbers
"""""""""""""""""""""""""

JSON has a single numeric type: number. JSON numbers are in the decimal system,
they can be positive and negative, they can have a fractional part, and they
can have an exponent. Numbers are unlimited in size. They are a
formalization of `scientific notation <http://en.wikipedia.org/wiki/Scientific_notation>`_.

A JSON number can be one of three things:

1. An integer
2. An arbitary-precision approximation of a `real number <http://en.wikipedia.org/wiki/Real_number>`_
3. An exact decimal fraction

The first two cases represent general purpose numbers, the third is a specialized
numeric type, useful for accounting and scientific software -- software that
requires exact numbers and is tied to the decimal system.

.. note::

    The latest version of the JSON spec, `RFC 7159 <http://tools.ietf.org/html/rfc7159.html>`_
    does not require implementations to support arbitrary-precision decimals,
    allowing them to sacrifice exactness and precision as they see fit. In fact,
    according that spec, the only *truly* interoperable numbers are integers
    ranging from -(2^53)+1 to (2^53)-1. This makes the author a very sad panda.

    Teleport's design is guided by JSON in its full, correct form, despite
    the fact that some JSON implementations could not support it. This is done
    partly because it is *The Right Thing* to do, and partly because
    implementing JSON correctly is not that difficult. For example, extra work
    must be performed to map JSON numbers to floats, whereas reading them
    correctly as decimals is trivial.

Floats vs. Decimals
"""""""""""""""""""

Floats are fixed-precision approximations of a real numbers, stored in a
non-trivial binary format allowing for very fast and reasonably correct
hardware calculations. Floats have been designed so well that for most inexact
arithmetic, a programmer will never run into their limitations. It is easy to
forget that floats are `a carefully crafted standard <http://en.wikipedia.org/wiki/IEEE_floating_point>`_,
not a fundamental number representation.

By default, the :mod:`json` module from the Python standard library maps
non-integer JSON numbers to floats. This is a practical design decision made by
most JSON software and Teleport supports it completely. Nevertheless, Teleport
does not define a Float type, opting instead for Decimal. Why is that?

There are two reasons: one philosophical and the other practical. The
philosophical reason is that JSON numbers simply *are* decimals, for better or
for worse. The practical reason is that mapping floats to decimals is not
trivial.

Consider the float value represented by ``1.1`` in Python. Because floats are
not stored in base 10, the actual value in memory looks more like this:

.. code-block:: python

    >>> (1.1).as_integer_ratio()
    (2476979795053773, 2251799813685248)

If you perform long division on these numbers, you will get a repeating decimal.
Needless to say, JSON numbers are not capable of representing this number
exactly, the best we can do is represent it with slightly more precision than
the underlying float, so it could be unambiguously parsed back into its
original binary form.

If you need exact float representations, then this hex string is by far the
simplest, most robust option:

.. code-block:: python

    >>> (1.1).hex()
    '0x1.199999999999ap+0'

However, floats were designed for *inexact* arithmetic, for which purpose
the Decimal type with its arbitrary precision is perfectly adequate. An exact
float representation is conceivably useful, but only for low-level hacks, which
are outside of the scope of this project.

Accounting Software
"""""""""""""""""""

Floats are not acceptable for representing currency values in accounting
software. It is possible to implement correct accounting algorithms using
floats, but if you wish to do it, be prepared to write mathematical proofs.

Currency values are fixed-precision decimals, so they can be represented
trivially and safely using Teleport's Decimal type. It should be noted that by
making this choice, you are limiting yourself to those implementations of JSON
which support arbitrary-precision decimals, like Python's :mod:`json` module.

.. _on-datetime-standards:

On DateTime Standards
---------------------

RFC 3339 is a `profile <http://en.wikipedia.org/wiki/Profile_(engineering)>`_
(a subset) of `ISO 8601 <http://www.iso.org/iso/home/standards/iso8601.htm>`_,
which is *the* worldwide standard for datetimes. Unlike its parent standard,
RFC 3339 is fairly minimalist, and since every RFC 3339 string is a valid
ISO 8601 string, it is very interoperable.

.. _on-timezones:

On Timezones and Offsets
""""""""""""""""""""""""

The DateTime type, along with RFC 3339 which defines it, is used to represent
*timestamps*, that is, points on a global, absolute timeline.

A full datetime string really contains two pieces of data: a clock reading,
and a time offset. A datetime with no such offset (a *naive* datetime) is not
suitable as a timestamp. In some cases, the offset was not recorded, but the
timestamps were presumably made in the same location. In these cases naive
datetimes can still have some use, which is why they are supported by RFC 3339
and therefore Teleport as well.

In accordance with RFC 3339, offsets are specified in hours and minutes.
While they do correspond to timezones, the correspondence is so unbelievably
complicated that timezones are omitted altogether from the Python standard
library. If you must deal with them, you can use the excellent
`pytz <http://pytz.sourceforge.net/>`_ library, but do not expect
interoperability from it.

Usually, the geographical information implied by the offset is irrelevant, in
which case you want to use `UTC <http://en.wikipedia.org/wiki/Coordinated_Universal_Time>`_,
or Coordinated Universal Time (offset 00:00). UTC quacks like a timezone but
really it represents the absence of one: it is not tied to any geographical
location and while it happens to match British clocks, it does so only in
winter.

