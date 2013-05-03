Teleport
========

.. currentmodule:: teleport

.. data:: types

   A dictionary mapping type names to serializer classes. By default, contains
   the following members: 
   ``"integer"`` (:class:`Integer`),
   ``"float"`` (:class:`Float`),
   ``"boolean"`` (:class:`Boolean`),
   ``"string"`` (:class:`String`),
   ``"binary"`` (:class:`Binary`),
   ``"array"`` (:class:`Array`),
   ``"struct"`` (:class:`Struct`) and
   ``"schema"`` (:class:`Schema`).

.. autoclass:: ValidationError
   :members:

.. autoclass:: Integer
   :members:

.. autoclass:: Float
   :members:

.. autoclass:: Boolean
   :members:

.. autoclass:: String
   :members:

.. autoclass:: Binary
   :members:

.. autoclass:: Array

   .. automethod:: serialize
   .. automethod:: deserialize
   .. automethod:: serialize_self
   .. automethod:: deserialize_self

.. autoclass:: Struct

   .. automethod:: serialize
   .. automethod:: deserialize
   .. automethod:: serialize_self
   .. automethod:: deserialize_self

.. autoclass:: Schema

   .. automethod:: serialize
   .. automethod:: deserialize
