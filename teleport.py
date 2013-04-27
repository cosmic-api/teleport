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


class Template(object):
    def normalize_data(self, datum):
        return self.deserialize(datum)
    def serialize_data(self, datum):
        return self.serialize(datum)

class IntegerTemplate(Template):

    def deserialize(self, datum):
        if type(datum) == int:
            return datum
        if type(datum) == float and datum.is_integer():
            return int(datum)
        raise ValidationError("Invalid integer", datum)

    def serialize(self, datum):
        return datum



class FloatTemplate(Template):

    def deserialize(self, datum):
        if type(datum) == float:
            return datum
        if type(datum) == int:
            return float(datum)
        raise ValidationError("Invalid float", datum)

    def serialize(self, datum):
        return datum



class StringTemplate(Template):

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



class BinaryTemplate(Template):

    def deserialize(self, datum):
        if type(datum) in (str, unicode,):
            try:
                return base64.b64decode(datum)
            except TypeError:
                raise ValidationError("Invalid base64 encoding", datum)
        raise ValidationError("Invalid binary data", datum)

    def serialize(self, datum):
        return base64.b64encode(datum)



class BooleanTemplate(Template):

    def deserialize(self, datum):
        if type(datum) == bool:
            return datum
        raise ValidationError("Invalid boolean", datum)

    def serialize(cls, datum):
        return datum



class ArrayTemplate(object):

    def __init__(self, items):
        self.items = items        

    def deserialize(self, datum):
        if type(datum) == list:
            ret = []
            for i, item in enumerate(datum):
                try:
                    ret.append(self.items.normalize_data(item))
                except ValidationError as e:
                    e.stack.append(i)
                    raise
            return ret
        raise ValidationError("Invalid array", datum)

    def serialize(self, datum):
        return [self.items.serialize_data(item) for item in datum]




class StructTemplate(object):

    def __init__(self, fields):
        self.fields = fields

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
                        ret[prop] = schema.normalize_data(datum[prop])
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
                ret[name] = prop['schema'].serialize_data(datum[name])
        return ret



class SchemaTemplate(Template):

    def serialize(self, datum):
        if isinstance(datum, Template):
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
        else:
            return datum.serialize()

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
            "schema": SchemaTemplate
        }

        template_cls = templates.get(st, None)
        if template_cls:
            return template_cls()

        # Simple model?
        simple = [
            ArraySchema,
            StructSchema
        ]
        for simple_cls in simple:
            if st == simple_cls.match_type:
                return simple_cls.normalize(datum)

        raise ValidationError("Unknown type", st)



class SimpleSchema(object):

    def __init__(self, opts={}):
        self.data = opts

    @classmethod
    def validate(cls, datum):
        pass

    @classmethod
    def normalize(cls, datum):
        # Normalize against model schema
        schema = cls.get_schema()
        datum = schema.normalize_data(datum)
        cls.validate(datum)
        return cls.instantiate(datum)

    @classmethod
    def instantiate(cls, datum):
        return cls(datum)

    def serialize(self):
        s = {
            "type": self.match_type
        }
        s.update(self.get_schema().serialize_data(self.data))
        return s

    def normalize_data(self, datum):
        if hasattr(self, "template_cls"):
            return self.template_cls(**self.data).deserialize(datum)
        return self.model_cls.normalize(datum, **self.data)

    def serialize_data(self, datum):
        if hasattr(self, "template_cls"):
            return self.template_cls(**self.data).serialize(datum)
        return self.model_cls.serialize(datum, **self.data)

    @classmethod
    def get_schema(cls):
        return StructSchema([])




class StructSchema(SimpleSchema):
    template_cls = StructTemplate
    match_type = "struct"

    def __init__(self, fields):
        super(StructSchema, self).__init__({
            "fields": fields
        })

    @classmethod
    def instantiate(cls, datum):
        return cls(datum["fields"])

    @classmethod
    def get_schema(cls):
        return StructSchema([
            field("type", StringTemplate()),
            field("fields", ArraySchema(StructSchema([
                field("name", StringTemplate()),
                field("schema", SchemaTemplate())
            ])))
        ])

    @classmethod
    def validate(cls, datum):
        """Raises :exc:`~cosmic.exception.ValidationError` if there are two
        fields with the same name.
        """
        super(StructSchema, cls).validate(datum)
        # Additional validation to check for duplicate fields
        fields = [field["name"] for field in datum['fields']]
        if len(fields) > len(set(fields)):
            raise ValidationError("Duplicate fields")



class ArraySchema(SimpleSchema):
    template_cls = ArrayTemplate
    match_type = u"array"

    def __init__(self, fields):
        super(ArraySchema, self).__init__({
            "items": fields
        })

    @classmethod
    def instantiate(cls, datum):
        return cls(datum["items"])

    @classmethod
    def get_schema(cls):
        return StructSchema([
            field("items", SchemaTemplate())
        ])



