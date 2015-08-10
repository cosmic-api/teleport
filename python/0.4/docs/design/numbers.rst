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

