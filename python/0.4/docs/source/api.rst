API Reference
=============

.. :currentmodule:: teleport

Type Classes
------------

What is called *type* in the specification is represented in this
implementation by subclasses of :class:`~teleport.Type`. *Type instances*,
conveniently, are instances of those classes.

.. autoclass:: teleport.Type
   :members:
   :undoc-members:

.. autoclass:: teleport.ConcreteType
   :members:
   :undoc-members:

.. autoclass:: teleport.GenericType
   :members:
   :undoc-members:

.. data:: teleport.CORE_TYPES

    A dict mapping type names to subclasses of :class:`~teleport.Type`.
    When this class gets instantiated, the type map is initiated with types
    taken from this dict.

    .. code-block:: python

        >>> from teleport import CORE_TYPES
        >>> CORE_TYPES
        {'Array': teleport.core.ArrayType,
         'Boolean': teleport.core.BooleanType,
         'DateTime': teleport.core.DateTimeType,
         'Decimal': teleport.core.DecimalType,
         'Integer': teleport.core.IntegerType,
         'JSON': teleport.core.JSONType,
         'Map': teleport.core.MapType,
         'Schema': teleport.core.SchemaType,
         'String': teleport.core.StringType,
         'Struct': teleport.core.StructType}


The t Function
--------------

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

Exceptions
----------

.. autoclass:: teleport.Undefined
   :members:
