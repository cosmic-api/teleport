import base64
from collections import OrderedDict

from werkzeug.local import LocalStack


class TypeMap(object):
    """Teleport is made extendable by allowing the application to define a
    custom mapping of type names (strings such as ``"Integer"``) to serializer
    classes. I could have defined a global mapping object for all applications
    to share, like Python's own :keyword:`sys.modules`, but this would
    prohibit multiple Teleport extentions to operate in clean isolation.
    Global state is evil, and Teleport successfully avoids it using Werkzeug's
    brilliant `Context Locals <http://werkzeug.pocoo.org/docs/local/>`_.

    First, let's create a type by defining a serializer::

        class Suit(object):
            match_type = "suit"

            def from_json(self, datum):
                if datum not in ["hearts", "spades", "clubs", "diamonds"]:
                    raise ValidationError("Invalid suit", datum)
                return datum

            def to_json(self, datum):
                return datum

    To extend Teleport with your custom type, subclass :class:`TypeMap`::

        class PokerTypeMap(TypeMap):

            def __getitem__(self, name):
                if name == "suit":
                    return Suit
                else:
                    return BUILTIN_TYPES[name]

    :class:`PokerTypeMap` is an extention of Teleport, to enable it within
    a specific code block, use Python's :keyword:`with` statement::

        # Only built-in types accessible here
        with PokerTypeMap():
            # Built-in types as well as "suit" are accessible
            with TypeMap():
                # Only built-in types here
                pass

    To avoid repeating this :keyword:`with` statement, put it at the entry
    point of your program. If your program is a WSGI server, use the
    :meth:`middleware` method to set the mapping for the entire
    application.

    If you are planning to serialize schemas containing custom types, Teleport
    will use the :attr:`match_type` attribute::

        >>> Schema.to_json(Suit())
        {'type': 'suit'}

    When you deserialize it (whether it is done by the same program or by a
    different program entirely), you need to ensure it will have access to
    the custom types that you defined.
    """

    def __getitem__(self, name):
        return BUILTIN_TYPES[name]

    def middleware(self, wsgi_app):
        """To use in `Flask <http://flask.pocoo.org/>`_::

            app = Flask(__name__)

            app.wsgi_app = PokerTypeMap().middleware(app.wsgi_app)
            app.run()

        In `Django <https://www.djangoproject.com/>`_ (see the
        auto-generated ``wsgi.py`` module)::

            from django.core.wsgi import get_wsgi_application
            application = get_wsgi_application()
            application = PokerTypeMap().middleware(application)

        """
        def wrapped(environ, start_response):
            with self:
                return wsgi_app(environ, start_response)
        return wrapped

    def __enter__(self):
        _ctx_stack.push(self)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        _ctx_stack.pop()


_ctx_stack = LocalStack()
# If no TypeMap is found on the stack, use the global object
_global_map = TypeMap()

def _get_current_map():
    if _ctx_stack.top != None:
        return _ctx_stack.top
    else:
        return _global_map


# Some syntax sugar
def required(name, schema):
    return (name, {"schema": schema, "required": True},)

def optional(name, schema):
    return (name, {"schema": schema, "required": False},)


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



class ParametrizedWrapper(object):

    def from_json(self, datum):
        datum = self.schema.from_json(datum)
        return self.inflate(datum)

    def to_json(self, datum):
        datum = self.deflate(datum)
        return self.schema.to_json(datum)

    def inflate(self, datum): # pragma: no cover
        return datum

    def deflate(self, datum): # pragma: no cover
        return datum



class BasicWrapper(object):

    @classmethod
    def from_json(cls, datum):
        datum = cls.schema.from_json(datum)
        return cls.inflate(datum)

    @classmethod
    def to_json(cls, datum):
        datum = cls.deflate(datum)
        return cls.schema.to_json(datum)

    @classmethod
    def inflate(cls, datum): # pragma: no cover
        return datum

    @classmethod
    def deflate(cls, datum): # pragma: no cover
        return datum



class Integer(object):
    match_type = "Integer"

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

    @staticmethod
    def to_json(datum):
        return datum



class Float(object):
    match_type = "Float"

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

    @staticmethod
    def to_json(datum):
        return datum



class String(object):
    match_type = "String"

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

    @staticmethod
    def to_json(datum):
        return datum



class Binary(object):
    match_type = "Binary"

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
        return base64.b64encode(datum)



class Boolean(object):
    match_type = "Boolean"

    @staticmethod
    def from_json(datum):
        """If *datum* is a boolean, return it. Otherwise, raise a
        :exc:`ValidationError`.
        """
        if type(datum) == bool:
            return datum
        raise ValidationError("Invalid Boolean", datum)

    @staticmethod
    def to_json(datum):
        return datum



class Box(object):
    """Used as a wrapper around JSON data to disambugate None as a JSON value
    (``null``) from None as an absense of value. Its :attr:`datum` attribute
    will hold the actual JSON value.

    For example, an HTTP request body may be empty in which case your function
    may return ``None`` or it may be "null", in which case the function can
    return a :class:`Box` instance with ``None`` inside.
    """
    def __init__(self, datum):
        self.datum = datum



class JSON(object):
    match_type = "JSON"

    @staticmethod
    def from_json(datum):
        """Return the JSON value wrapped in a :class:`Box`.
        """
        return Box(datum)

    @staticmethod
    def to_json(datum):
        return datum.datum



class Array(object):
    """The argument *param* is a serializer that defines the type of each item
    in the array.
    """
    match_type = "Array"

    def __init__(self, param):
        self.param = param

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



class Struct(object):
    """*param* must be a list of dicts, where each dict has three items:
    *name* (String), *schema* (serializer) and *required* (Boolean). For each
    pair, *schema* is used to serialize and deserialize a dictionary value
    matched by the key *name*.
    """
    match_type = "Struct"

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



class Map(object):
    """The argument *param* is a serializer that defines the type of each item
    in the map.
    """
    match_type = "Map"

    def __init__(self, param):
        self.param = param

    def from_json(self, datum):
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
    """
    match_type = "OrderedMap"

    def __init__(self, param):
        self.param = param
        self.schema = Struct([
            required(u"map", Map(param)),
            required(u"order", Array(String))
        ])

    def inflate(self, datum):
        order = datum["order"]
        keys = datum["map"].keys()
        if len(order) != len(keys) or set(order) != set(keys):
            raise ValidationError("Invalid OrderedMap", datum)
        # Turn into OrderedDict instance
        ret = OrderedDict()
        for key in order:
            ret[key] = datum["map"][key]
        return ret

    def deflate(self, datum):
        return {
            "map": dict(datum.items()),
            "order": datum.keys()
        }



class Schema(object):
    match_type = "Schema"

    @staticmethod
    def to_json(datum):
        """If the serializer passed in as *datum* has a :meth:`serialize_self`
        method, use it. Otherwise, return a simple schema by finding the type
        in the serializer's :attr:`match_type` attribute.
        """
        param_schema = _get_current_map()[datum.match_type][1]
        if param_schema != None:
            return {
                "type": datum.match_type,
                "param": param_schema.to_json(datum.param)
            }
        else:
            return {"type": datum.match_type}

    @staticmethod
    def from_json(datum):
        """Datum must be a dict with a key *type* that has a string value.
        This value will me passed into the :meth:`get` method of the current
        :class:`TypeMap` instance to get the matching serializer. If no serializer
        is found, :exc:`UnknownTypeValidationError` will be raised.
        """
        # Peek into dict struct to get the type
        if type(datum) != dict or "type" not in datum.keys():
            raise ValidationError("Invalid Schema", datum)

        t = datum["type"]

        # Try to get the serializer class from the current TypeMap
        try:
            serializer, param_schema = _get_current_map()[t]
        except KeyError:
            raise UnknownTypeValidationError("Unknown type", t)

        # Deserialize or instantiate
        if param_schema != None:
            param = param_schema.from_json(datum["param"])
            return serializer(param)
        else:
            return serializer



BUILTIN_TYPES = {
    "Integer": (Integer, None),
    "Float": (Float, None),
    "String": (String, None),
    "Binary": (Binary, None),
    "Boolean": (Boolean, None),
    "Schema": (Schema, None),
    "JSON": (JSON, None),
    "Array": (Array, Schema),
    "Map": (Map, Schema),
    "OrderedMap": (OrderedMap, Schema),
    "Struct": (Struct, OrderedMap(Struct([
        required(u"schema", Schema),
        required(u"required", Boolean)
    ])))
}
