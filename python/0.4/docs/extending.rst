Extending Teleport
------------------

Teleport's specification does not define the totality of the
:func:`t() <teleport.TypeMap.__call__>` function, just provides some instances
of its inputs and outputs. Any implementation is allowed to extend it with new
instances, inventing new concrete types, new generic types or other
higher-level constructs.

This implementation provides a convenient interface for extending Teleport with
new concrete and generic types. You can see how it works by reading through
the following recipes, but first, in order to keep the global namespace clean,
make your own personal instance of the :func:`t` function:

.. code-block:: python

    from teleport import TypeMap, ConcreteType, GenericType

    t = TypeMap()

Save this in your project's package, say, in ``types.py``. To use your extended
version of Teleport, simply import your version of :data:`t`:

.. code-block:: python

    from jsonapp.types import t

.. note::

    All these recipes are taken verbatim from the :mod:`teleport.examples`
    module. You can play around with them in your REPL:

    .. code-block:: python

        >>> from teleport.examples import t

Recipe: Color
^^^^^^^^^^^^^

Let's add a concrete type that matches hex-encoded colors. Use the
:meth:`~teleport.TypeMap.register` decorator to add a new type to your
:data:`t` instance:

.. code-block:: python

    @t.register("Color")
    class ColorType(ConcreteType):

        def check(self, value):
            if not t("String").check(value):
                return False

            return re.compile('^#[0-9a-f]{6}$').match(value) is not None

Once we have called :meth:`~teleport.TypeMap.register`, we can use the new
type as a first-class citizen:

.. code-block:: python

    >>> t("Color").check('#ffffff')
    True
    >>> t("Color").check('yellow')
    False
    >>> t({"Array": "Color"}).check(['#ffffff', '#000000']))
    True

If you don't provide your own :meth:`~teleport.Type.from_json` and
:meth:`~teleport.Type.to_json` implementations, the default implementation
assumes that the native form is the same as the JSON form:

.. code-block:: python

    >>> t("Color").from_json('#ffffff')
    "#ffffff"

If your purpose for defining custom types is primarily type-checking, then you
can forget about those methods altogether, serialization will still work.

Recipe: PythonObject
^^^^^^^^^^^^^^^^^^^^

The :mod:`pickle` module from Python's standard library provides generic
serialization of Python objects. Even though :mod:`pickle` makes the author
nervous, we will use it to give Teleport the same power:

.. code-block:: python

    import pickle

    @t.register("PythonObject")
    class PythonObjectType(ConcreteType):

        def from_json(self, json_value):
            if not t("String").check(json_value):
                raise Undefined("PythonObject must be a string")
            try:
                return pickle.loads(json_value)
            except:
                raise Undefined("PythonObject could not be unpickled")

        def to_json(self, native_value):
            return pickle.dumps(native_value)

Note that if we implement :meth:`~teleport.Type.from_json`, implementing
:meth:`~teleport.Type.check` is not necessary, as long as the former behaves
correctly by raising :exc:`~teleport.Undefined`.

Now we can use it to serialize most Python objects:

.. code-block:: python

    >>> t("PythonObject").to_json(set([1, 2]))
    'c__builtin__\nset\np0\n((lp1\nI1\naI2\natp2\nRp3\n.'

.. warning::

    Never unpickle data coming from an untrusted or unauthenticated source.

Recipe: Nullable
^^^^^^^^^^^^^^^^

Teleport does not encourage using null unless there is a very good reason for
it. One good reason is an existing format that uses it. Either way, the
following generic type is a good way to introduce it:

.. code-block:: python

    @t.register("Nullable")
    class NullableType(GenericType):

        def process_param(self, param):
            self.child = self.t(param)

        def from_json(self, value):
            if value is None:
                return None
            return self.child.from_json(value)

        def to_json(self, value):
            if value is None:
                return None
            return self.child.to_json(value)

Now you can define weird types like this:

.. code-block:: python

    >>> s = t({"Array": {"Nullable": "String"}})
    >>> s.check(["sparse", None, "arrays", None, None, None, "what"])
    True

More realistically, you might use it to deal with JSON objects with null
values. The reason this type is not in Teleport core is to discourage us from
creating these monsters:

.. code-block:: python

    >>> s = t({"Struct": {
    ...          "required": {"id": "Integer"},
    ...          "optional": {"name": {"Nullable": "String"},
    ...                       "age":  {"Nullable": "Integer"}}}})

Even though they may be useful for reading objects like these:

.. code-block:: python

    >>> s.check({"id": 1, "name": "Jake", "age": 28})
    True
    >>> s.check({"id": 1, "name": None, "age": 12})
    True
    >>> s.check({"id": 1, "age": None})
    True
