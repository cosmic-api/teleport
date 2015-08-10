TypeMap Instances
=================

The Teleport specification defines a mathematical function t, which maps
type definitions to type instances. In Teleport, this mapping is performed
by instances of :class:`~teleport.TypeMap`. These instances behave like
functions and the :func:`t` function that you import from the :mod:`teleport`
module is actually an instance of this class:

.. code-block:: python

>>> from teleport import t
>>> t
<teleport.core.TypeMap at 0x7ffcb08e7c10>


.. autoclass:: teleport.TypeMap
:members:
:special-members: __call__
