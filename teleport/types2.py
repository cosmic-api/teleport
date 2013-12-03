import json
import base64
import isodate

try:
    from collections import OrderedDict
except ImportError:
    # Python 2.6 or earlier
    from ordereddict import OrderedDict





    
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


# Some syntax sugar
def required(name, schema, doc=None):
    return {"name": name, "schema": schema, "required": True, "doc": doc}

def optional(name, schema, doc=None):
    return {"name": name, "schema": schema, "required": False, "doc": doc}


    
class NewType(object):
    param_schema = None

    def __init__(self, schema):
        self.schema = schema

    def __repr__(self):
        return self.type_name

    def to_json(self, datum):
        return datum

    def from_json(self, datum):
        return datum

    
class NewTypeParametrized(NewType):

    def __call__(self, param):
        return Serializer(self.schema, self.type_name, param)

class NewTypeWrapper(NewType):

    def _ensure_inner_schema(self):
        if not hasattr(self, "_inner_schema"):
            self._inner_schema = self.get_inner_schema()

    def to_json(self, datum, param=None):
        self._ensure_inner_schema()
        if param is None:
            return self._inner_schema.to_json(self.disassemble(datum))
        else:
            return self._inner_schema.to_json(self.disassemble(datum, param))
            
    def from_json(self, datum, param=None):
        self._ensure_inner_schema()
        if param is None:
            return self.assemble(self._inner_schema.from_json(datum))
        else:
            return self.assemble(self._inner_schema.from_json(datum), param)


class Serializer(object):
    "A thing that wraps the type and turns it into a serializer"

    def __init__(self, schema, type_name, param=None):
        self.schema = schema
        self.type_name = type_name
        self.param = param

    def from_json(self, datum):
        if self.param is not None:
            return self.schema.types[self.type_name].from_json(datum, self.param)
        else:
            return self.schema.types[self.type_name].from_json(datum)

    def to_json(self, datum):
        if self.param is not None:
            return self.schema.types[self.type_name].to_json(datum, self.param)
        else:
            return self.schema.types[self.type_name].to_json(datum)

    def __repr__(self):
        if self.param is not None:
            return "%s(%s)" % (self.type_name, repr(self.param))
        else:
            return self.type_name

    def as_json(self):
        if self.param is not None:
            return {str(self.type_name): self.schema.types[self.type_name].param_schema.to_json(self.param)}
        else:
            return self.type_name



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





class SchemaType(object):
    type_name = 'Schema'
    param_schema = None

    def __init__(self):
        self.types = {
            "Schema": self
        }

    def export_globals(self):
        ret = {}
        for type_name, type_object in self.types.items():
            if type_object.param_schema is not None:
                ret[type_name] = type_object
            else:
                ret[type_name] = self.T(type_name)
        return ret

    def T(self, type_name, param=None):
        return Serializer(self, type_name, param)

    def get_type(self, name):
        try:
            return self.types[name]
        except KeyError:
            raise ValidationError("Cannot find type", name)

    def to_json(self, datum):
        """If given a serializer representing a simple type, return a JSON
        object with a single attribute *type*, if a parametrized one,
        also include an attribute *param*.

        By default *type* is the class name of the serializer, but it
        can be overridden by the serializer's :data:`type_name`
        property.

        """
        return datum.as_json()

    def from_json(self, datum):
        """Expects a JSON object with a *type* attribute and an optional
        *param* attribute. Uses *type* to find the serializer. If the type
        is simple, returns the serializer, if parametrized, deserializes
        *param* and uses it to instatiate the serializer class before
        returning it.

        After looking in the built-in types, this method will attempt
        to find the serializer via *type_getter*, an argument of
        :func:`standard_types`. See :ref:`extending-teleport`. If no
        serializer is found, :exc:`UnknownTypeValidationError` will be
        raised.

        """
        if type(datum) in (unicode, str):
            t = datum
            serializer = self.get_type(t)
            if serializer.param_schema is not None:
                raise ValidationError("Missing param for %s schema" % t)
            return Serializer(self, t)
        if type(datum) == dict and len(datum) == 1:
            t = datum.keys()[0]
            serializer = self.get_type(t)
            if serializer.param_schema is None:
                raise ValidationError("Unexpected param for %s schema" % t)
            param = serializer.param_schema.from_json(datum[t])
            return Serializer(self, t, param)
        raise ValidationError("Invalid Schema", datum)



class IntegerType(NewType):
    type_name = "Integer"

    def from_json(self, datum):
        """If *datum* is an integer, return it; if it is a float with a 0 for
        its fractional part, return the integer part as an
        int. Otherwise, raise a :exc:`ValidationError`.

        """
        if type(datum) == int:
            return datum
        if type(datum) == float and datum.is_integer():
            return int(datum)
        raise ValidationError("Invalid Integer", datum)

    def to_json(self, datum):
        return datum


        
class FloatType(NewType):
    type_name = "Float"

    def from_json(self, datum):
        """If *datum* is a float, return it; if it is an integer, cast it to a
        float and return it. Otherwise, raise a
        :exc:`ValidationError`.

        """
        if type(datum) == float:
            return datum
        if type(datum) == int:
            return float(datum)
        raise ValidationError("Invalid Float", datum)



class StringType(NewType):
    type_name = "String"

    def from_json(self, datum):
        """If *datum* is of unicode type, return it. If it is a string, decode
        it as UTF-8 and return the result. Otherwise, raise a
        :exc:`ValidationError`. Unicode errors are dealt with strictly
        by raising :exc:`UnicodeDecodeValidationError`, a subclass of
        the above.

        """
        if type(datum) == unicode:
            return datum
        if type(datum) == str:
            try:
                return datum.decode('utf_8')
            except UnicodeDecodeError as inst:
                raise UnicodeDecodeValidationError(unicode(inst))
        raise ValidationError("Invalid String", datum)



class BinaryType(NewType):
    """This type may be useful when you wish to send a binary file. The
    byte string will be base64-encoded for safety.

        >>> b = open('pixel.png', 'rb').read()
        >>> Binary.to_json(b)
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAACXBIWXMAAAsTAAALE
        wEAmpwYAAAAB3RJTUUH3QoSBggTmj6VgAAAABl0RVh0Q29tbWVudABDcmVhdGVkIHd
        pdGggR0lNUFeBDhcAAAAMSURBVAjXY/j//z8ABf4C/tzMWecAAAAASUVORK5CYII='

    """
    type_name = "Binary"

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



class BooleanType(NewType):
    type_name = "Boolean"

    def from_json(self, datum):
        """If *datum* is a boolean, return it. Otherwise, raise a
        :exc:`ValidationError`.

        """
        if type(datum) == bool:
            return datum
        raise ValidationError("Invalid Boolean", datum)



class DateTimeType(NewTypeWrapper):
    """Wraps the :class:`String` type.

            >>> DateTime.to_json(datetime.now())
            u'2013-10-18T01:58:24.904349'

    """
    type_name = "DateTime"

    def get_inner_schema(self):
        return self.schema.T('String')

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



class JSONType(NewType):
    """This type may be used as a kind of wildcard that will accept any
    JSON value and return it untouched. Presumably you still want to
    interpret the meaning of this arbitrary JSON data, you just don't
    want to do it through Teleport.

    """

    def from_json(self, datum):
        """Return the JSON value wrapped in a :class:`Box`.
        """
        return Box(datum)

    def to_json(self, datum):
        return datum.datum


class ArrayType(NewTypeParametrized):
    """The argument *param* is a serializer that defines the type of each
    item in the array.

    """
    type_name = "Array"

    def __init__(self, schema):
        self.param_schema = schema.T('Schema')
        super(ArrayType, self).__init__(schema)

    def from_json(self, datum, inner_type):
        """If *datum* is a list, construct a new list by putting each element
        of *datum* through a serializer provided as *param*. This serializer
        may raise a :exc:`ValidationError`. If *datum* is not a
        list, :exc:`ValidationError` will also be raised.
        """
        if type(datum) == list:
            ret = []
            for i, item in enumerate(datum):
                try:
                    ret.append(inner_type.from_json(item))
                except ValidationError as e:
                    e.stack.append(i)
                    raise
            return ret
        raise ValidationError("Invalid Array", datum)

    def to_json(self, datum, inner_type):
        """Serialize each item in the *datum* iterable using *param*. Return
        the resulting values in a list.
        """
        return [inner_type.to_json(item) for item in datum]


class TupleType(NewTypeParametrized):
    """The argument *param* is a serializer that defines the type of each item
    in the array.
    """
    type_name = "Tuple"

    def __init__(self, schema):
        self.param_schema = schema.T('Array', schema.T('Schema'))
        super(TupleType, self).__init__(schema)

    def assemble(self, datum, inner_types):
        if type(datum) in [tuple, list]:
            if len(datum) != len(inner_types):
                raise ValidationError("Invalid Tuple, wrong number of arguments", datum)
            ret = []
            for i, item in enumerate(datum):
                try:
                    ret.append(inner_types[i].from_json(item))
                except ValidationError as e:
                    e.stack.append(i)
                    raise
            return ret
        raise ValidationError("Invalid Tuple", datum)

    def disassemble(self, datum, inner_types):
        ret = []
        for i, item in enumerate(datum):
            ret.append(inner_types[i].to_json(item))
        return ret



class MapType(NewTypeParametrized):
    """The argument *param* is a serializer that defines the type of each item
    in the map.
    """
    type_name = "Map"

    def __init__(self, schema):
        self.param_schema = schema.T('Schema')
        super(MapType, self).__init__(schema)

    def from_json(self, datum, inner_type):
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
                    ret[key] = inner_type.from_json(val)
                except ValidationError as e:
                    e.stack.append(key)
                    raise
            return ret
        raise ValidationError("Invalid Map", datum)
            

    def to_json(self, datum, inner_type):
        ret = {}
        for key, val in datum.items():
            ret[key] = inner_type.to_json(val)
        return ret



class StructType(NewTypeParametrized):
    """*param* must be an :class:`OrderedDict`, where the keys are field
    names, and values are dicts with two items: *schema* (serializer) and
    *required* (Boolean). For each pair, *schema* is used to serialize and
    deserialize a dict value matched by the corresponding key.

    For convenience, :class:`Struct` can be instantiated with a list of tuples
    like the constructor of :class:`OrderedDict`.
    """
    type_name = "Struct"
    def __init__(self, schema):

        self.param_schema = schema.T('Array', schema.T('Struct', [
            required(u"name", schema.T('String')),
            required(u"schema", schema.T('Schema')),
            required(u"required", schema.T('Boolean')),
            optional(u"doc", schema.T('String'))
        ]))

        def assemble(self, datum):
            names = set()
            for item in datum:
                names.add(item['name'])
            if len(names) < len(datum):
                raise ValidationError("Names cannot repeat")
            return datum

        super(StructType, self).__init__(schema)


    def from_json(self, datum, fields):
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
            for field in fields:
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
        raise ValidationError("Invalid Struct", datum)


    def to_json(self, datum, fields):
        ret = {}
        for field in fields:
            name = field['name']
            schema = field['schema']
            if name in datum.keys() and datum[name] != None:
                ret[name] = schema.to_json(datum[name])
        return ret





def standard_types(schema):
    return {
        "Integer": IntegerType(schema),
        "Float": FloatType(schema),
        "String": StringType(schema),
        "Binary": BinaryType(schema),
        "Boolean": BooleanType(schema),
        "DateTime": DateTimeType(schema),
        "JSON": JSONType(schema),

        "Array": ArrayType(schema),
        "Struct": StructType(schema),
        "Map": MapType(schema),
    }


Schema = SchemaType()
T = Schema.T
Schema.types.update(standard_types(Schema))

globals().update(Schema.export_globals())



