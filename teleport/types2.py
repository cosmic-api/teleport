
class ValidationError(Exception):
    pass




    
class NewType(object):
    param_schema = None

    def __init__(self, schema):
        self.schema = schema

    def __repr__(self):
        return self.type_name


class TypeParameterPair(object):
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

    
class NewTypeParametrized(NewType):

    def __call__(self, param):
        return TypeParameterPair(self.schema, self.type_name, param)





class SchemaType(object):
    type_name = 'Schema'

    def __init__(self):
        self.types = types = {
            "Schema": self
        }

    def T(self, type_name, param=None):
        return TypeParameterPair(self, type_name, param)

    def get_type(self, name):
        try:
            return self.types[name]
        except KeyError:
            raise ValidationError("Cannot find type", name)

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
            serializer = self.get_type(t)
            if serializer.param_schema is not None:
                raise ValidationError("Missing param for %s schema" % t)
            return serializer
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



class ArrayType(NewTypeParametrized):
    """The argument *param* is a serializer that defines the type of each item
    in the array.
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
    }


Schema = SchemaType()
T = Schema.T
Schema.types.update(standard_types(Schema))

globals().update(Schema.types)



