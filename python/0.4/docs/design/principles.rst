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
