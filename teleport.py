import sys
import json
import base64
from copy import deepcopy

def field(name, schema):
    return {
        "name": name,
        "schema": schema
    }

class ValidationError(Exception):
    """Raised by the model system. Stores the location of the error in the
    JSON document relative to its root for a more useful stack trace.

    First parameter is the error *message*, second optional parameter is the
    struct that failed validation.
    """

    def __init__(self, message, *args):
        super(ValidationError, self).__init__(message)
        self.stack = []
        # Just the message or was there also an struct passed in?
        self.has_obj = len(args) > 0
        if self.has_obj:
            self.obj = args[0]

    def _print_with_format(self, func):
        # Returns the full error message with the representation
        # of its literals determined by the passed in function.
        ret = ""
        # If there is a stack, preface the message with a location
        if self.stack:
            stack = ""
            for item in reversed(self.stack):
                stack += '[' + func(item) + ']'
            ret += "Item at %s " % stack
        # Main message
        ret += self.message
        # If an struct was passed in, represent it at the end
        if self.has_obj:
            ret += ": %s" % func(self.obj)
        return ret

    def __str__(self):
        return self._print_with_format(repr)

    def print_json(self):
        """Print the same message as the one you would find in a
        console stack trace, but using JSON to output all the language
        literals. This representation is used for sending error
        messages over the wire.
        """
        return self._print_with_format(json.dumps)

class UnicodeDecodeValidationError(ValidationError):
    """A subclass of :exc:`~cosmic.exceptions.ValidationError` raised
    in place of a :exc:`UnicodeDecodeError`.
    """



class IntegerTemplate(object):
    match_type = "integer"

    def deserialize(self, datum):
        if type(datum) == int:
            return datum
        if type(datum) == float and datum.is_integer():
            return int(datum)
        raise ValidationError("Invalid integer", datum)

    def serialize(self, datum):
        return datum



class FloatTemplate(object):
    match_type = "float"

    def deserialize(self, datum):
        if type(datum) == float:
            return datum
        if type(datum) == int:
            return float(datum)
        raise ValidationError("Invalid float", datum)

    def serialize(self, datum):
        return datum



class StringTemplate(object):
    match_type = "string"

    def deserialize(self, datum):
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



class BinaryTemplate(object):
    match_type = "binary"

    def deserialize(self, datum):
        if type(datum) in (str, unicode,):
            try:
                return base64.b64decode(datum)
            except TypeError:
                raise ValidationError("Invalid base64 encoding", datum)
        raise ValidationError("Invalid binary data", datum)

    def serialize(self, datum):
        return base64.b64encode(datum)



class BooleanTemplate(object):
    match_type = "array"

    def deserialize(self, datum):
        if type(datum) == bool:
            return datum
        raise ValidationError("Invalid boolean", datum)

    def serialize(cls, datum):
        return datum



class ArrayTemplate(object):
    match_type = "array"

    def __init__(self, items):
        self.items = self.data = items        

    def deserialize(self, datum):
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
        return [self.items.serialize(item) for item in datum]

    @classmethod
    def get_params(cls):
        return StructTemplate([
            field("items", SchemaTemplate())
        ])

    def serialize_self(self):
        s = {"type": "array"}
        s.update(ArrayTemplate.get_params().serialize({"items": self.items}))
        return s

    @classmethod
    def deserialize_self(self, datum):
        opts = ArrayTemplate.get_params().deserialize(datum)
        return ArrayTemplate(opts["items"])


class StructTemplate(object):
    match_type = "struct"

    def __init__(self, fields):
        self.fields = self.data = fields

    def deserialize(self, datum):
        if type(datum) == dict:
            ret = {}
            props = {}
            for prop in self.fields:
                props[prop["name"]] = prop["schema"]
            extra = set(datum.keys()) - set(props.keys())
            if extra:
                raise ValidationError("Unexpected fields", list(extra))
            for prop, schema in props.items():
                if prop in datum.keys():
                    try:
                        ret[prop] = schema.deserialize(datum[prop])
                    except ValidationError as e:
                        e.stack.append(prop)
                        raise
            return ret
        raise ValidationError("Invalid struct", datum)

    def serialize(self, datum):
        ret = {}
        for prop in self.fields:
            name = prop['name']
            if name in datum.keys() and datum[name] != None:
                ret[name] = prop['schema'].serialize(datum[name])
        return ret

    @classmethod
    def get_params(cls):
        return StructTemplate([
            field("type", StringTemplate()),
            field("fields", ArrayTemplate(StructTemplate([
                field("name", StringTemplate()),
                field("schema", SchemaTemplate())
            ])))
        ])

    def serialize_self(self):
        s = {"type": "struct"}
        s.update(StructTemplate.get_params().serialize({"fields": self.fields}))
        return s

    @classmethod
    def deserialize_self(cls, datum):
        opts = StructTemplate.get_params().deserialize(datum)
        # Additional validation to check for duplicate fields
        fields = [field["name"] for field in opts["fields"]]
        if len(fields) > len(set(fields)):
            raise ValidationError("Duplicate fields")
        return StructTemplate(opts["fields"])



class SchemaTemplate(object):

    def serialize(self, datum):
        if hasattr(datum, "serialize_self"):
            return datum.serialize_self()

        return {
            "type": {
                IntegerTemplate: "integer",
                FloatTemplate: "float",
                StringTemplate: "string",
                BinaryTemplate: "binary",
                BooleanTemplate: "boolean",
                SchemaTemplate: "schema"
            }[datum.__class__]
        }

    def deserialize(self, datum):
        # Peek into the struct before letting the real models
        # do proper validation
        if type(datum) != dict or "type" not in datum.keys():
            raise ValidationError("Invalid schema", datum)

        datum = deepcopy(datum)
        st = datum.pop("type")

        templates = {
            "integer": IntegerTemplate,
            "float": FloatTemplate,
            "string": StringTemplate,
            "binary": BinaryTemplate,
            "boolean": BooleanTemplate,
            "schema": SchemaTemplate,
            "array": ArrayTemplate,
            "struct": StructTemplate
        }


        template_cls = templates.get(st, None)
        if template_cls:
            if hasattr(template_cls, "deserialize_self"):
                return template_cls.deserialize_self(datum)
            return template_cls()

        raise ValidationError("Unknown type", st)


