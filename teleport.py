import base64
from collections import OrderedDict



# Some syntax sugar
def required(name, schema, doc=None):
    return (name, {"schema": schema, "required": True, "doc": doc})

def optional(name, schema, doc=None):
    return (name, {"schema": schema, "required": False, "doc": doc})


class ValidationError(Exception):
    """Raised during desearialization. Stores the location of the error in the
    JSON document relative to its root.

    First argument is the error message, second optional argument is the
    object that failed validation.
    """

    def __init__(self, message, *args):
        self.message = message
        self.stack = []
        # Just the message or was there also an object passed in?
        self.has_obj = len(args) > 0
        if self.has_obj:
            self.obj = args[0]

    def __str__(self):
        ret = ""
        # If there is a stack, preface the message with a location
        if self.stack:
            stack = ""
            for item in reversed(self.stack):
                stack += '[' + repr(item) + ']'
            ret += "Item at %s " % stack
        # Main message
        ret += self.message
        # If an struct was passed in, represent it at the end
        if self.has_obj:
            ret += ": %s" % repr(self.obj)
        return ret

class UnicodeDecodeValidationError(ValidationError):
    pass

class UnknownTypeValidationError(ValidationError):
    pass



class BasicWrapper(object):
    param_schema = None

    @classmethod
    def from_json(cls, datum):
        datum = cls.schema.from_json(datum)
        return cls.assemble(datum)

    @classmethod
    def to_json(cls, datum):
        datum = cls.disassemble(datum)
        return cls.schema.to_json(datum)

    @classmethod
    def assemble(cls, datum): # pragma: no cover
        return datum

    @classmethod
    def disassemble(cls, datum): # pragma: no cover
        return datum



class ParametrizedWrapper(object):

    def from_json(self, datum):
        datum = self.schema.from_json(datum)
        return self.assemble(datum)

    def to_json(self, datum):
        datum = self.disassemble(datum)
        return self.schema.to_json(datum)

    def assemble(self, datum): # pragma: no cover
        return datum

    def disassemble(self, datum): # pragma: no cover
        return datum



class BasicPrimitive(object):
    param_schema = None

    @staticmethod
    def from_json(datum): # pragma: no cover
        return datum

    @staticmethod
    def to_json(datum): # pragma: no cover
        return datum



class ParametrizedPrimitive(object):

    def __init__(self, param):
        self.param = param



class Box(object):
    """Used as a wrapper around JSON data to disambiguate None as a JSON value
    (``null``) from None as an absense of value. Its :attr:`datum` attribute
    will hold the actual JSON value.

    For example, an HTTP request body may be empty in which case your function
    may return ``None`` or it may be "null", in which case the function can
    return a :class:`Box` instance with ``None`` inside.
    """
    def __init__(self, datum):
        self.datum = datum




def standard_types(type_getter=None, include=None):

    class Schema(BasicPrimitive):

        @staticmethod
        def to_json(datum):
            """Find the serializer in the current :class:`TypeMap` based on the
            class name, or :attr:`type_name` attribute, if such exists.
            """
            # Type name is declared explicitly
            if hasattr(datum, "type_name"):
                type_name = datum.type_name
            # If datum is a class, use its name
            elif datum.__class__ == type:
                type_name = datum.__name__
            # Otherwise assume it's an instance
            else:
                type_name = datum.__class__.__name__
            if datum.param_schema != None:
                return {
                    "type": type_name,
                    "param": datum.param_schema.to_json(datum.param)
                }
            else:
                return {"type": type_name}

        @staticmethod
        def from_json(datum):
            """Datum must be a dict with a key *type* that has a string value.
            This value will me passed into the :meth:`__getitem__` method of the
            current :class:`TypeMap` instance to get the matching serializer. If
            no serializer is found, :exc:`UnknownTypeValidationError` will be
            raised.
            """
            # Peek into dict struct to get the type
            if type(datum) != dict or "type" not in datum.keys():
                raise ValidationError("Invalid Schema", datum)

            t = datum["type"]

            # Try to get the serializer class from the current TypeMap
            try:
                serializer = BUILTIN_TYPES.get(t, None)
                if serializer is None:
                    if type_getter is not None:
                        serializer = type_getter(t)
                    else:
                        raise KeyError()
            except KeyError:
                raise UnknownTypeValidationError("Unknown type", t)

            if serializer.param_schema and "param" not in datum:
                raise ValidationError("Missing param for %s schema" % t)

            if not serializer.param_schema and "param" in datum:
                raise ValidationError("Unexpected param for %s schema" % t)

            # Deserialize or instantiate
            if serializer.param_schema != None:
                param = serializer.param_schema.from_json(datum["param"])
                return serializer(param)
            else:
                return serializer



    class Integer(BasicPrimitive):

        @staticmethod
        def from_json(datum):
            """If *datum* is an integer, return it; if it is a float with a 0 for
            its fractional part, return the integer part as an int. Otherwise,
            raise a :exc:`ValidationError`.
            """
            if type(datum) == int:
                return datum
            if type(datum) == float and datum.is_integer():
                return int(datum)
            raise ValidationError("Invalid Integer", datum)



    class Float(BasicPrimitive):

        @staticmethod
        def from_json(datum):
            """If *datum* is a float, return it; if it is an integer, cast it to a
            float and return it. Otherwise, raise a :exc:`ValidationError`.
            """
            if type(datum) == float:
                return datum
            if type(datum) == int:
                return float(datum)
            raise ValidationError("Invalid Float", datum)



    class String(BasicPrimitive):

        @staticmethod
        def from_json(datum):
            """If *datum* is of unicode type, return it. If it is a string, decode
            it as UTF-8 and return the result. Otherwise, raise a
            :exc:`ValidationError`. Unicode errors are dealt
            with strictly by raising :exc:`UnicodeDecodeValidationError`, a
            subclass of the above.
            """
            if type(datum) == unicode:
                return datum
            if type(datum) == str:
                try:
                    return datum.decode('utf_8')
                except UnicodeDecodeError as inst:
                    raise UnicodeDecodeValidationError(unicode(inst))
            raise ValidationError("Invalid String", datum)



    class Binary(BasicPrimitive):

        @staticmethod
        def from_json(datum):
            """If *datum* is a base64-encoded string, decode and return it. If not
            a string, or encoding is wrong, raise :exc:`ValidationError`.
            """
            if type(datum) in (str, unicode,):
                try:
                    return base64.b64decode(datum)
                except TypeError:
                    raise ValidationError("Invalid base64 encoding", datum)
            raise ValidationError("Invalid Binary data", datum)

        @staticmethod
        def to_json(datum):
            "Encode *datum* using base64."
            return base64.b64encode(datum)



    class Boolean(BasicPrimitive):

        @staticmethod
        def from_json(datum):
            """If *datum* is a boolean, return it. Otherwise, raise a
            :exc:`ValidationError`.
            """
            if type(datum) == bool:
                return datum
            raise ValidationError("Invalid Boolean", datum)



    class JSON(BasicPrimitive):

        @staticmethod
        def from_json(datum):
            """Return the JSON value wrapped in a :class:`Box`.
            """
            return Box(datum)

        @staticmethod
        def to_json(datum):
            return datum.datum



    class Array(ParametrizedPrimitive):
        """The argument *param* is a serializer that defines the type of each item
        in the array.
        """
        param_schema = Schema

        def from_json(self, datum):
            """If *datum* is a list, construct a new list by putting each element
            of *datum* through a serializer provided as *param*. This serializer
            may raise a :exc:`ValidationError`. If *datum* is not a
            list, :exc:`ValidationError` will also be raised.
            """
            if type(datum) == list:
                ret = []
                for i, item in enumerate(datum):
                    try:
                        ret.append(self.param.from_json(item))
                    except ValidationError as e:
                        e.stack.append(i)
                        raise
                return ret
            raise ValidationError("Invalid Array", datum)

        def to_json(self, datum):
            """Serialize each item in the *datum* iterable using *param*. Return
            the resulting values in a list.
            """
            return [self.param.to_json(item) for item in datum]



    class Map(ParametrizedPrimitive):
        """The argument *param* is a serializer that defines the type of each item
        in the map.
        """
        param_schema = Schema

        def from_json(self, datum):
            """If *datum* is a dict, deserialize it, otherwise raise a
            :exc:`ValidationError`. The keys of the dict must be unicode, and the
            values will be deserialized using *param*.
            """
            if type(datum) == dict:
                ret = {}
                for key, val in datum.items():
                    if type(key) != unicode:
                        raise ValidationError("Map key must be unicode", key)
                    try:
                        ret[key] = self.param.from_json(val)
                    except ValidationError as e:
                        e.stack.append(key)
                        raise
                return ret
            raise ValidationError("Invalid Map", datum)

        def to_json(self, datum):
            ret = {}
            for key, val in datum.items():
                ret[key] = self.param.to_json(val)
            return ret



    class OrderedMap(ParametrizedWrapper):
        """The argument *param* is a serializer that defines the type of each item
        in the map.

        Internal schema::

            Struct([
                required(u"map", Map(param)),
                required(u"order", Array(String))
            ])

        The order of the items in *map* is not preserved by JSON, hence the
        existence of *order*, an array of keys in *map*.
        """
        param_schema = Schema

        def __init__(self, param):
            self.param = param
            self.schema = Struct([
                required(u"map", Map(param)),
                required(u"order", Array(String))
            ])

        def assemble(self, datum):
            """:exc:`ValidationError` is raised if *order* does not correspond to
            the keys in *map*. The native form is Python's :class:`OrderedDict`.
            """
            order = datum["order"]
            keys = datum["map"].keys()
            if len(order) != len(keys) or set(order) != set(keys):
                raise ValidationError("Invalid OrderedMap", datum)
            # Turn into OrderedDict instance
            ret = OrderedDict()
            for key in order:
                ret[key] = datum["map"][key]
            return ret

        def disassemble(self, datum):
            return {
                "map": dict(datum.items()),
                "order": datum.keys()
            }



    class Struct(ParametrizedPrimitive):
        """*param* must be an :class:`OrderedDict`, where the keys are field
        names, and values are dicts with two items: *schema* (serializer) and
        *required* (Boolean). For each pair, *schema* is used to serialize and
        deserialize a dict value matched by the corresponding key.

        For convenience, :class:`Struct` can be instantiated with a list of tuples
        like the constructor of :class:`OrderedDict`.
        """

        def __init__(self, param):
            if type(param) == list:
                param = OrderedDict(param)
            self.param = param

        def from_json(self, datum):
            """If *datum* is a dict, deserialize it against *param* and return
            the resulting dict. Otherwise raise a :exc:`ValidationError`.

            A :exc:`ValidationError` will be raised if:

            1. *datum* is missing a required field
            2. *datum* has a field not declared in *param*.
            3. One of the values of *datum* does not pass validation as defined
               by the *schema* of the corresponding field.
            """
            if type(datum) == dict:
                ret = {}
                required = {}
                optional = {}
                for name, field in self.param.items():
                    if field["required"] == True:
                        required[name] = field["schema"]
                    else:
                        optional[name] = field["schema"]
                missing = set(required.keys()) - set(datum.keys())
                if missing:
                    raise ValidationError("Missing fields", list(missing))
                extra = set(datum.keys()) - set(required.keys() + optional.keys())
                if extra:
                    raise ValidationError("Unexpected fields", list(extra))
                for field, schema in optional.items() + required.items():
                    if field in datum.keys():
                        try:
                            ret[field] = schema.from_json(datum[field])
                        except ValidationError as e:
                            e.stack.append(field)
                            raise
                return ret
            else:
                raise ValidationError("Invalid Struct", datum)

        def to_json(self, datum):
            ret = {}
            for name, field in self.param.items():
                schema = field['schema']
                if name in datum.keys() and datum[name] != None:
                    ret[name] = schema.to_json(datum[name])
            return ret

    Struct.param_schema = OrderedMap(Struct([
        required(u"schema", Schema),
        required(u"required", Boolean),
        optional(u"doc", String)
    ]))


    if include is None:
        include = [
            'Binary', 'Struct', 'Map', 'Float', 'JSON', 'Boolean',
            'Integer', 'Array', 'Schema', 'OrderedMap', 'String'
        ]

    BUILTIN_TYPES = {}
    for name in include:
        BUILTIN_TYPES[name] = locals()[name]

    return BUILTIN_TYPES

globals().update(standard_types())
