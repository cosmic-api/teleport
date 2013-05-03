import json
import base64

def field(name, schema):
    return {
        "name": name,
        "schema": schema
    }

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



class Integer(object):

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

    def deserialize(self, datum):
        """If *datum* is of unicode type, return it. Note that strings of str
        type needs to be decoded.
        """
        if type(datum) == unicode:
            return datum
        if type(datum) == str:
            raise ValidationError("Invalid string. Expected unicode, got str", datum)
        raise ValidationError("Invalid string", datum)

    def serialize(self, datum):
        return datum



class Binary(object):

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

    def deserialize(self, datum):
        """If *datum* is a boolean, return it. Otherwise, raise a
        :exc:`ValidationError`.
        """
        if type(datum) == bool:
            return datum
        raise ValidationError("Invalid boolean", datum)

    def serialize(cls, datum):
        return datum



class Array(object):
    """The argument *items* is a serializer that defines the type of each item
    in the array.
    """

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
            field("type", String()),
            field("items", Schema())
        ])

    def serialize_self(self):
        s = {"type": "array"}
        s.update(Array.get_params().serialize({"items": self.items}))
        return s

    @classmethod
    def deserialize_self(self, datum):
        opts = Array.get_params().deserialize(datum)
        return Array(opts["items"])



class Struct(object):
    """*fields* must be a list of dicts, where each dict has two items: *name*
    (string), and *schema* (serializer). For each pair, *schema* is used to
    serialize and deserialize a dictionary value matched by the key *name*.
    """

    def __init__(self, fields):
        self.fields = fields

    def deserialize(self, datum):
        """If *datum* is a dict, deserialize it against *fields* and return
        the resulting dict. Otherwise raise a :exc:`ValidationError`.

        A :exc:`ValidationError` will be raised if:

        1. *datum* has a property not declared in *fields*.
        2. One of the values of *datum* does not pass validation as defined
           by the corresponding *schema*.
        """
        if type(datum) == dict:
            ret = {}
            fields = {}
            for field in self.fields:
                fields[field["name"]] = field["schema"]
            extra = set(datum.keys()) - set(fields.keys())
            if extra:
                raise ValidationError("Unexpected fields", list(extra))
            for name, schema in fields.items():
                if name in datum.keys():
                    try:
                        ret[name] = schema.deserialize(datum[name])
                    except ValidationError as e:
                        e.stack.append(name)
                        raise
            return ret
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
            field("type", String()),
            field("fields", Array(Struct([
                field("name", String()),
                field("schema", Schema())
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

    def serialize(self, datum):
        """If the serializer passed in as *datum* has a :meth:`serialize_self`
        method, use it. Otherwise, return a simple schema by finding the type
        in the global :data:`types` object.
        """
        if hasattr(datum, "serialize_self"):
            return datum.serialize_self()
        else:
            for t, cls in types.items():
                if datum.__class__ == cls:
                    return {"type": t}
            raise KeyError("Teleport is unfamiliar with serializer %s" % datum)

    def deserialize(self, datum):
        """Datum must be a dict with a key *type* that has a string value,
        which is used to find a serializer class in :data:`types`. If this
        serializer defines a :meth:`deserialize_self` method, *datum* will be
        passed into this method in order to deserialize it. Otherwise, the
        serializer will be instantiated with no arguments. The instance is
        returned.
        """
        # Peek into dict struct to get the type
        if type(datum) != dict or "type" not in datum.keys():
            raise ValidationError("Invalid schema", datum)

        t = datum["type"]

        # Try to fetch the serializer class
        try:
            serializer = types[t]
        except KeyError:
            raise ValidationError("Unknown type", t)

        # Deserialize or instantiate
        if hasattr(serializer, "deserialize_self"):
            return serializer.deserialize_self(datum)
        else:
            return serializer()


types = {
    "integer": Integer,
    "float": Float,
    "string": String,
    "binary": Binary,
    "boolean": Boolean,
    "schema": Schema,
    "array": Array,
    "struct": Struct
}
