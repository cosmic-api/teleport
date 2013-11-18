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
            return serializer(param)
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




def standard_types(schema):
    return {
        "Integer": IntegerType(schema),
        "Array": ArrayType(schema),
        "Float": FloatType(schema),
        "String": StringType(schema),
        "Binary": BinaryType(schema),
        "Boolean": BooleanType(schema),
        "DateTime": DateTimeType(schema),
        "JSON": JSONType(schema),
    }


Schema = SchemaType()
T = Schema.T
Schema.types.update(standard_types(Schema))

globals().update(Schema.export_globals())



