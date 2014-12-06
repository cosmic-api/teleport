Design Notes
============

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
^^^^^^^^^^^^^^^^^^^^^^^^

The DateTime type, along with RFC 3339 which defines it, is used to represent
*timestamps*, that is, instances in time.

A full datetime string really contains two pieces of data: an instant in time,
and a time offset. A datetime with no such offset (a *naive* datetime) is not
suitable as a timestamp. Naive datetimes are silly and not supported by this
implementation of Teleport.

In accordance with RFC 3339, offsets are specified in hours and minutes.
While they do correspond to timezones, the correspondence is so complicated
that timezones are omitted altogether from the Python standard library. If you
must deal with them, you can use the excellent
`pytz <http://pytz.sourceforge.net/>`_ library, but do not expect
interoperability from it.

Usually, the geographical information presented by the offset is irrelevant, in
which case you want to use `UTC <http://en.wikipedia.org/wiki/Coordinated_Universal_Time>`_,
or Coordinated Universal Time (offset 00:00). UTC quacks like a timezone but
really it represents the absence of one: it is not tied to any geographical
location and while it happens to match British clocks, it does so only in
winter.

.. _on-numeric-types:

On Numeric Types
----------------

.. seealso::

    The two built-in numeric types: :ref:`type-integer` and :ref:`type-decimal`.

JSON has a single numeric type: number. JSON numbers are in the decimal system,
they can be positive and negative, they can have a fractional part, and they
can have an exponent. Numbers are unlimited in size. JSON numbers are a
formalization of
`scientific notation <http://en.wikipedia.org/wiki/Scientific_notation>`_.

A JSON number is either:

1. A `rational number <http://en.wikipedia.org/wiki/Rational_number>`_ with a non-repeating decimal expansion
2. An arbitary-precision approximation of a `real number <http://en.wikipedia.org/wiki/Real_number>`_

In the context of non-mathematical software, the only useful rational numbers
are integers. In the rare case that precise rational numbers are needed, JSON
number will not help you since it cannot represent numbers as simple as 1/3.

So, we come to the unsurprising conclusion that JSON numbers are either
integers or floats. Teleport has an Integer type, but its second
numeric type is called Decimal, not Float. Why is that?

Decimals vs. Floats
^^^^^^^^^^^^^^^^^^^

A Python float (`same goes for most other floats <http://en.wikipedia.org/wiki/IEEE_floating_point>`_) is either:

1. One of about 2^64 rational numbers (this usage is almost always a mistake)
2. A fixed-precision approximation of a real number

By default, the :mod:`json` module from the Python standard library maps
non-integer JSON numbers to floats. This is a practical design decision made by
most JSON software. However, mapping between JSON numbers and floats as done
by Python is not trivial.

Consider the float value represented by ``1.1`` in Python. Because floats are
stored in memory as *binary*, not decimal fractions, the actual value in memory
looks more like this:

.. code-block:: python

    >>> (1.1).as_integer_ratio()
    (2476979795053773, 2251799813685248)

Which is a big repeating decimal:

.. code-block:: python

    >>> from decimal import Decimal
    >>> Decimal('2476979795053773') / Decimal('2251799813685248')
    Decimal('1.100000000000000088817841970012523233890533447265625')

There is no way to represent this number using a JSON number, the closest we
can get is an approximation with a certain precision, which is what Python
does when you JSON-encode a float:

.. code-block:: python

    >>> json.dumps(1.1)
    '1.1'

This behavior is implementation specific.

The 2008 version of `IEEE floating point standard <http://en.wikipedia.org/wiki/IEEE_floating_point>`_
defines standard decimal representations for its float types, which can be used
as the basis for an exact mapping between JSON numbers and floats, however,
implementing this correctly is much more difficult than arbitrary-precision
decimals and the usefulness (aside from low-level hacks) is dubious.

In conclusion, Teleport avoids the name Float because JSON numbers are *not*
floats, they are decimals. A Float type is conceivable as part of an extention
of Teleport.

Accounting Software
^^^^^^^^^^^^^^^^^^^

Floats are not acceptable for representing currency values in accounting
software. It is possible to implement correct accounting algorithms using
floats, but if you wish to do it, be prepared to write mathematical proofs.

Currency values are fixed-precision decimals, so they can be represented
trivially and safely using Teleport's Decimal type. It should be noted that by
making this choice, you are limiting yourself to those implementations of JSON
which support arbitrary-precision decimals, like Python's :mod:`json` module.

.. note::

    The latest version of the JSON spec, `RFC 7159 <http://tools.ietf.org/html/rfc7159.html>`_
    does not require implementations to support arbitrary-precision decimals,
    allowing them to pick any precision they choose. The author believes in
    correctness over convenience so this design choice makes the author a very
    sad panda.

.. _decimal-precision:

Using Teleport with Precision
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If precision is important for you, you'll be happy to know that Python comes
with a built-in :class:`~decimal.Decimal` class whose instances can be mapped
perfectly to JSON numbers. Moreover, the :mod:`json` module makes it easy to
use them instead of floats:

.. code-block:: python

    >>> import decimal
    >>> json.loads('{"price": 0.99}', parse_float=decimal.Decimal)
    {u'price': Decimal('0.99')}

