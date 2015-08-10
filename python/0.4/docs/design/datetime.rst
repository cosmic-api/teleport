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
