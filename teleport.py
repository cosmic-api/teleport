import json
import base64
from werkzeug.local import LocalStack


class TypeMap(object):
    """Teleport is made extendable by allowing the application to define a
    custom mapping of type names (strings such as ``"integer"``) to serializer
    classes. I could have defined a global mapping object for all applications
    to share, like Python's own :keyword:`sys.modules`, but this would
    prohibit multiple Teleport extentions to operate in clean isolation.
    Global state is evil, and Teleport successfully avoids it using Werkzeug's
    brilliant `Context Locals <http://werkzeug.pocoo.org/docs/local/>`_.

    First, let's create a type by defining a serializer::

        class Suit(object):
            match_type = "suit"

            def deserialize(self, datum):
                if datum not in ["hearts", "spades", "clubs", "diamonds"]:
                    raise ValidationError("Invalid suit", datum)
                return datum

            def serialize(self, datum):
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

        >>> Schema().serialize(Suit())
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

# Some syntax sugar
def required(name, schema):
    return {"name": name, "schema": schema, "required": True}

def optional(name, schema):
    return {"name": name, "schema": schema, "required": False}


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


class Integer(object):
    match_type = "integer"

    def deserialize(self, datum):
        """If *datum* is an integer, return it; if it is a float with a 0 for
        its fractional part, return the integer part as an int. Otherwise,
        raise a :exc:`ValidationError`.
        """
        if type(datum) == int:
            return datum
        if type(datum) == float and datum.is_integer():
            return int(datum)
        raise ValidationError("Invalid integer", datum)

    def serialize(self, datum):
        return datum



class Float(object):
    match_type = "float"

    def deserialize(self, datum):
        """If *datum* is a float, return it; if it is an integer, cast it to a
        float and return it. Otherwise, raise a :exc:`ValidationError`.
        """
        if type(datum) == float:
            return datum
        if type(datum) == int:
            return float(datum)
        raise ValidationError("Invalid float", datum)

    def serialize(self, datum):
        return datum



class String(object):
    match_type = "string"

    def deserialize(self, datum):
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
        raise ValidationError("Invalid string", datum)

    def serialize(self, datum):
        return datum



class Binary(object):
    match_type = "binary"

    def deserialize(self, datum):
        """If *datum* is a base64-encoded string, decode and return it. If not
        a string, or encoding is wrong, raise :exc:`ValidationError`.
        """
        if type(datum) in (str, unicode,):
            try:
                return base64.b64decode(datum)
            except TypeError:
                raise ValidationError("Invalid base64 encoding", datum)
        raise ValidationError("Invalid binary data", datum)

    def serialize(self, datum):
        return base64.b64encode(datum)



class Boolean(object):
    match_type = "boolean"

    def deserialize(self, datum):
        """If *datum* is a boolean, return it. Otherwise, raise a
        :exc:`ValidationError`.
        """
        if type(datum) == bool:
            return datum
        raise ValidationError("Invalid boolean", datum)

    def serialize(cls, datum):
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
    match_type = "json"

    def deserialize(self, datum):
        """Return the JSON value wrapped in a :class:`Box`.
        """
        return Box(datum)

    def serialize(self, datum):
        return datum.datum



class Array(object):
    """The argument *items* is a serializer that defines the type of each item
    in the array.
    """
    match_type = "array"

    def __init__(self, items):
        self.items = items        

    def deserialize(self, datum):
        """If *datum* is a list, construct a new list by putting each element
        of *datum* through a serializer provided as *items*. This serializer
        may raise a :exc:`ValidationError`. If *datum* is not a
        list, :exc:`ValidationError` will also be raised.
        """
        if type(datum) == list:
            ret = []
            for i, item in enumerate(datum):
                try:
                    ret.append(self.items.deserialize(item))
                except ValidationError as e:
                    e.stack.append(i)
                    raise
            return ret
        raise ValidationError("Invalid array", datum)

    def serialize(self, datum):
        """Serialize each item in the *datum* iterable using *items*. Return
        the resulting values in a list.
        """
        return [self.items.serialize(item) for item in datum]

    @classmethod
    def get_params(cls):
        return Struct([
            required("type", String()),
            required("items", Schema())
        ])

    def serialize_self(self):
        s = {"type": "array"}
        s.update(Array.get_params().serialize({"items": self.items}))
        return s

    @classmethod
    def deserialize_self(cls, datum):
        opts = Array.get_params().deserialize(datum)
        return Array(opts["items"])



class Map(object):
    """The argument *items* is a serializer that defines the type of each item
    in the map.
    """
    match_type = "map"

    def __init__(self, items):
        self.items = items        

    def deserialize(self, datum):
        if type(datum) == dict:
            ret = {}
            for key, val in datum.items():
                if type(key) != unicode:
                    raise ValidationError("Map key must be unicode", key)
                try:
                    ret[key] = self.items.deserialize(val)
                except ValidationError as e:
                    e.stack.append(i)
                    raise
            return ret
        raise ValidationError("Invalid map", datum)

    def serialize(self, datum):
        return [self.items.serialize(item) for item in datum]

    @classmethod
    def get_params(cls):
        return Struct([
            required("type", String()),
            required("items", Schema())
        ])

    def serialize_self(self):
        s = {"type": "map"}
        s.update(Map.get_params().serialize({"items": self.items}))
        return s

    @classmethod
    def deserialize_self(cls, datum):
        opts = Map.get_params().deserialize(datum)
        return Map(opts["items"])



class Struct(object):
    """*fields* must be a list of dicts, where each dict has three items:
    *name* (string), *schema* (serializer) and *required* (boolean). For each
    pair, *schema* is used to serialize and deserialize a dictionary value
    matched by the key *name*.
    """
    match_type = "struct"

    def __init__(self, fields):
        self.fields = fields

    def deserialize(self, datum):
        """If *datum* is a dict, deserialize it against *fields* and return
        the resulting dict. Otherwise raise a :exc:`ValidationError`.

        A :exc:`ValidationError` will be raised if:

        1. *datum* is missing a required field
        2. *datum* has a field not declared in *fields*.
        3. One of the values of *datum* does not pass validation as defined
           by the *schema* of the corresponding field.
        """
        if type(datum) == dict:
            ret = {}
            required = {}
            optional = {}
            for field in self.fields:
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
                        ret[field] = schema.deserialize(datum[field])
                    except ValidationError as e:
                        e.stack.append(field)
                        raise
            return ret
        else:
            raise ValidationError("Invalid struct", datum)

    def serialize(self, datum):
        ret = {}
        for field in self.fields:
            name = field['name']
            schema = field['schema']
            if name in datum.keys() and datum[name] != None:
                ret[name] = schema.serialize(datum[name])
        return ret

    @classmethod
    def get_params(cls):
        return Struct([
            required("type", String()),
            required("fields", Array(Struct([
                required("name", String()),
                required("schema", Schema()),
                required("required", Boolean())
            ])))
        ])

    def serialize_self(self):
        s = {"type": "struct"}
        s.update(Struct.get_params().serialize({"fields": self.fields}))
        return s

    @classmethod
    def deserialize_self(cls, datum):
        opts = Struct.get_params().deserialize(datum)
        # Additional validation to check for duplicate fields
        fields = [field["name"] for field in opts["fields"]]
        if len(fields) > len(set(fields)):
            raise ValidationError("Duplicate fields")
        return Struct(opts["fields"])



class Schema(object):
    match_type = "schema"

    def serialize(self, datum):
        """If the serializer passed in as *datum* has a :meth:`serialize_self`
        method, use it. Otherwise, return a simple schema by finding the type
        in the serializer's :attr:`match_type` attribute.
        """
        if hasattr(datum, "serialize_self"):
            return datum.serialize_self()
        else:
            return {"type": datum.match_type}

    def deserialize(self, datum):
        """Datum must be a dict with a key *type* that has a string value.
        This value will me passed into the :meth:`get` method of the current
        :class:`TypeMap` instance to get the matching serializer. If no serializer
        is found, :exc:`UnknownTypeValidationError` will be raised.

        If this serializer defines a :meth:`deserialize_self` method, *datum*
        will be passed into items

        This function will use the serializer's :meth:`deserialize_self`
        instantiation method if such exists (*datum* will be passed into it).
        Otherwise, it will simply instantiate the serializer. Either way, the
        instance is returned.
        """
        # Peek into dict struct to get the type
        if type(datum) != dict or "type" not in datum.keys():
            raise ValidationError("Invalid schema", datum)

        t = datum["type"]

        # Try to get the serializer class from the current TypeMap
        try:
            if _ctx_stack.top != None:
                serializer = _ctx_stack.top[t]
            else:
                serializer = _global_map[t]
        except KeyError:
            raise UnknownTypeValidationError("Unknown type", t)

        # Deserialize or instantiate
        if hasattr(serializer, "deserialize_self"):
            return serializer.deserialize_self(datum)
        else:
            return serializer()


BUILTIN_TYPES = {
    "integer": Integer,
    "float": Float,
    "string": String,
    "binary": Binary,
    "boolean": Boolean,
    "schema": Schema,
    "json": JSON,
    "array": Array,
    "map": Map,
    "struct": Struct
}
