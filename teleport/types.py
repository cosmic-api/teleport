import json
import base64
import isodate

try:
    from collections import OrderedDict
except ImportError:
    # Python 2.6 or earlier
    from ordereddict import OrderedDict


# Some syntax sugar
def required(name, schema, doc=None):
    return {"name": name, "schema": schema, "required": True, "doc": doc}

def optional(name, schema, doc=None):
    return {"name": name, "schema": schema, "required": False, "doc": doc}


class ValidationError(Exception):
    """Raised during deserialization. Stores the location of the error in the
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
    def __init__(self, type_name):
        self.message = "Unknown type"
        self.has_obj = True
        self.obj = type_name
        self.stack = []


class Type(object):
    param_schema = None

    def __init__(self):
        pass

    def from_json(self, datum):
        return datum

    def to_json(self, datum):
        return datum



class Parametrized(Type):

    def __init__(self, param):
        self.param = param


class Wrapper(Type):
    
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


        


class Box(object):
    """Used as a wrapper around JSON data to disambiguate None as a JSON value
    (``null``) from None as an absence of value. Its :attr:`datum` attribute
    will hold the actual JSON value.

    For example, an HTTP request body may be empty in which case your function
    may return ``None`` or it may be "null", in which case the function can
    return a :class:`Box` instance with ``None`` inside.
    """
    def __init__(self, datum):
        self.datum = datum

    def __hash__(self):
        return hash(json.dumps(self.datum))

    def __eq__(self, datum):
        return self.datum == datum



def standard_types(type_getter=None, include=None):
    """
    :param type_getter: A function that, given a custom type name, returns the
        corresponding serializer.
    :param include: A list of names of the built-in serializers that you want to
        be included in your custom Teleport module.

    :returns: A dict, mapping class names to classes.
    """

    # type_getter is used here
    def get_serializer(t):
        if t in BUILTIN_TYPES:
            return BUILTIN_TYPES[t]
        if type_getter is not None:
            return type_getter(t)
        raise UnknownTypeValidationError(t)



    class JSONObject(Type):

        def from_json(self, datum):
            if type(datum) == dict:
                return datum
            raise ValidationError("Expecting JSON object", datum)


    class JSONArray(Type):

        def from_json(self, datum):
            if type(datum) == list:
                return datum
            raise ValidationError("Expecting JSON array", datum)



    class Schema(Type):

        def to_json(self, datum):
            """If given a serializer representing a simple type, return a JSON
            object with a single attribute *type*, if a parametrized one, also
            include an attribute *param*.

            By default *type* is the class name of the serializer, but it can
            be overridden by the serializer's :data:`type_name` property.
            """
            # If datum is a class, use its name
            if datum.__class__ == type:
                if hasattr(datum, "type_name"):
                    type_name = datum.type_name
                else:
                    type_name = datum.__name__
                return datum.__name__
            # Otherwise assume it's an instance
            if hasattr(datum, "type_name"):
                type_name = datum.type_name
            else:
                type_name = datum.__class__.__name__
            if datum.param_schema != None:
                return {
                    str(type_name): datum.param_schema.to_json(datum.param)
                }
            else:
                return type_name

        def from_json(self, datum):
            """Expects a JSON object with a *type* attribute and an optional
            *param* attribute. Uses *type* to find the serializer. If the type
            is simple, returns the serializer, if parametrized, deserializes
            *param* and uses it to instatiate the serializer class before
            returning it.

            After looking in the built-in types, this method will attempt to
            find the serializer via *type_getter*, an argument of
            :func:`standard_types`. See :ref:`extending-teleport`. If no
            serializer is found, :exc:`UnknownTypeValidationError` will be
            raised.
            """
            if type(datum) in (unicode, str):
                t = datum
                serializer = get_serializer(t)
                if serializer.param_schema is not None:
                    raise ValidationError("Missing param for %s schema" % t)
                return serializer()
            if type(datum) == dict and len(datum) == 1:
                t = datum.keys()[0]
                serializer = get_serializer(t)
                if serializer.param_schema is None:
                    raise ValidationError("Unexpected param for %s schema" % t)
                param = serializer.param_schema.from_json(datum[t])
                return serializer(param)
            raise ValidationError("Invalid Schema", datum)



    class Integer(Type):

        def from_json(self, datum):
            """If *datum* is an integer, return it; if it is a float with a 0 for
            its fractional part, return the integer part as an int. Otherwise,
            raise a :exc:`ValidationError`.
            """
            if type(datum) == int:
                return datum
            if type(datum) == float and datum.is_integer():
                return int(datum)
            raise ValidationError("Invalid Integer", datum)

        def to_json(self, datum):
            return datum



    class Float(Type):

        def from_json(self, datum):
            """If *datum* is a float, return it; if it is an integer, cast it to a
            float and return it. Otherwise, raise a :exc:`ValidationError`.
            """
            if type(datum) == float:
                return datum
            if type(datum) == int:
                return float(datum)
            raise ValidationError("Invalid Float", datum)



    class String(Type):

        def from_json(self, datum):
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



    class Binary(Type):
        """This type may be useful when you wish to send a binary file. The
        byte string will be base64-encoded for safety.

            >>> b = open('pixel.png', 'rb').read()
            >>> Binary.to_json(b)
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAACXBIWXMAAAsTAAALE
            wEAmpwYAAAAB3RJTUUH3QoSBggTmj6VgAAAABl0RVh0Q29tbWVudABDcmVhdGVkIHd
            pdGggR0lNUFeBDhcAAAAMSURBVAjXY/j//z8ABf4C/tzMWecAAAAASUVORK5CYII='

        """

        def from_json(self, datum):
            """If *datum* is a base64-encoded string, decode and return it. If not
            a string, or encoding is wrong, raise :exc:`ValidationError`.
            """
            if type(datum) in (str, unicode,):
                try:
                    return base64.b64decode(datum)
                except TypeError:
                    raise ValidationError("Invalid base64 encoding", datum)
            raise ValidationError("Invalid Binary data", datum)

        def to_json(self, datum):
            "Encode *datum* using base64."
            return base64.b64encode(datum)



    class Boolean(Type):

        def from_json(self, datum):
            """If *datum* is a boolean, return it. Otherwise, raise a
            :exc:`ValidationError`.
            """
            if type(datum) == bool:
                return datum
            raise ValidationError("Invalid Boolean", datum)



    class DateTime(Wrapper):
        """Wraps the :class:`String` type.

                >>> DateTime.to_json(datetime.now())
                u'2013-10-18T01:58:24.904349'

        """
        schema = String()

        def assemble(self, datum):
            """Parse *datum* as an ISO 8601-encoded time and return a
            :class:`datetime` object. If the string is invalid, raise a
            :exc:`ValidationError`.
            """
            try:
                return isodate.parse_datetime(datum)
            except (ValueError, isodate.isoerror.ISO8601Error) as e:
                raise ValidationError(e.args[0], datum)

        def disassemble(self, datum):
            """Given a datetime object, return an ISO 8601-encoded string.
            """
            return unicode(datum.isoformat())



    class JSON(Type):
        """This type may be used as a kind of wildcard that will accept any
        JSON value and return it untouched. Presumably you still want to
        interpret the meaning of this arbitrary JSON data, you just don't want
        to do it through Teleport.
        """

        def from_json(self, datum):
            """Return the JSON value wrapped in a :class:`Box`.
            """
            return Box(datum)

        def to_json(self, datum):
            return datum.datum



    class Array(Wrapper, Parametrized):
        """The argument *param* is a serializer that defines the type of each item
        in the array.
        """
        schema = JSONArray()
        param_schema = Schema()

        def assemble(self, datum):
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

        def disassemble(self, datum):
            """Serialize each item in the *datum* iterable using *param*. Return
            the resulting values in a list.
            """
            return [self.param.to_json(item) for item in datum]


    class ArrayParamType(Wrapper):
        schema = Schema()

        def assemble(self, datum):
            return Array(datum)

        def disassemble(self, datum):
            pass

            
    class Tuple(Wrapper, Parametrized):
        """The argument *param* is a serializer that defines the type of each item
        in the array.
        """
        param_schema = Array(Schema())
        schema = JSONArray()

        def assemble(self, datum):
            if len(datum) != len(self.param):
                raise ValidationError("Invalid Tuple, wrong number of arguments", datum)
            ret = []
            for i, item in enumerate(datum):
                schema = self.param[i]
                try:
                    ret.append(schema.from_json(item))
                except ValidationError as e:
                    e.stack.append(i)
                    raise
            return ret

        def disassemble(self, datum):
            ret = []
            for i, item in enumerate(datum):
                schema = self.param[i]
                ret.append(schema.to_json(item))
            return ret


            

    class Map(Wrapper, Parametrized):
        """The argument *param* is a serializer that defines the type of each item
        in the map.
        """
        schema = JSONObject()
        param_schema = Schema()

        def assemble(self, datum):
            """If *datum* is a dict, deserialize it, otherwise raise a
            :exc:`ValidationError`. The keys of the dict must be unicode, and the
            values will be deserialized using *param*.
            """
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

        def disassemble(self, datum):
            ret = {}
            for key, val in datum.items():
                ret[key] = self.param.to_json(val)
            return ret



    class OrderedMap(Wrapper, Parametrized):
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
        param_schema = Schema()

        def __init__(self, param):
            self.param = param
            self.schema = Struct([
                required(u"map", Map(param)),
                required(u"order", Array(String()))
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

    class Enum(Wrapper, Parametrized):
        schema = String()
        param_schema = Array(String())

        def __init__(self, param):
            self.param = param

        @classmethod
        def assemble(cls, datum):
            if datum not in cls.param:
                raise ValidationError("Illegal value for Enum", datum)
            return datum

    class Lazy(object):
        def __init__(self, schema):
            self._schema = schema
            self.schema = None
        def from_json(self, datum):
            if self.schema == None:
                self.schema = Schema().from_json(self._schema)
            return self.schema.from_json(datum)
        def to_json(self, datum):
            if self.schema == None:
                self.schema = Schema().from_json(self._schema)
            return self.schema.to_json(datum)


    class Struct(Wrapper, Parametrized):
        """*param* must be an :class:`OrderedDict`, where the keys are field
        names, and values are dicts with two items: *schema* (serializer) and
        *required* (Boolean). For each pair, *schema* is used to serialize and
        deserialize a dict value matched by the corresponding key.

        For convenience, :class:`Struct` can be instantiated with a list of tuples
        like the constructor of :class:`OrderedDict`.
        """
        schema = JSONObject()

        def assemble(self, datum):
            """If *datum* is a dict, deserialize it against *param* and return
            the resulting dict. Otherwise raise a :exc:`ValidationError`.

            A :exc:`ValidationError` will be raised if:

            1. *datum* is missing a required field
            2. *datum* has a field not declared in *param*.
            3. One of the values of *datum* does not pass validation as defined
               by the *schema* of the corresponding field.
            """
            ret = {}
            required = {}
            optional = {}
            for field in self.param:
                if field["required"] == True:
                    required[field["name"]] = field["schema"]
                else:
                    optional[field["name"]] = field["schema"]
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

        def disassemble(self, datum):
            ret = {}
            for field in self.param:
                name = field['name']
                schema = field['schema']
                if name in datum.keys() and datum[name] != None:
                    ret[name] = schema.to_json(datum[name])
            return ret

    class StructParam(Wrapper):
        schema = Array(Struct([
            required(u"name", String()),
            required(u"schema", Schema()),
            required(u"required", Boolean()),
            optional(u"doc", String())
        ]))
        __schema = Lazy({"Array":
            {"Struct": [
                {
                    'name': 'name',
                    'required': True,
                    'schema': 'String'
                },
                {
                    'name': 'schema',
                    'required': True,
                    'schema': 'Schema'
                },
                {
                    'name': 'required',
                    'required': True,
                    'schema': 'Boolean'
                },
                {
                    'name': 'doc',
                    'required': False,
                    'schema': 'String'
                }
            ]}
        })

        def assemble(self, datum):
            names = set()
            for item in datum:
                names.add(item['name'])
            if len(names) < len(datum):
                raise ValidationError("Names cannot repeat")
            return datum

    Struct.param_schema = StructParam()


    if include is None:
        include = [
            'Binary', 'Struct', 'Map', 'Float', 'JSON', 'Boolean',
            'Integer', 'Array', 'Schema', 'OrderedMap', 'String', 'DateTime',
            'Tuple', 'Enum'
        ]

    BUILTIN_TYPES = {}
    for name in include:
        BUILTIN_TYPES[name] = locals()[name]

    return BUILTIN_TYPES

globals().update(standard_types())

