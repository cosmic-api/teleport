import isodate


class Undefined(Exception):
    pass


class Type(object):
    """Conceptually, an instance of this class is a value space, a set of
    JSON values. As such, the only method defined by the Teleport specification
    is :meth:`contains`, everything else is extentions made by this
    implementation.

    """

    def contains(self, json_value):
        """
        Returns :data:`True` if *json_value* is a member of this type's value
        space and :data:`False` if it is not.

        .. code-block:: python

            >>> t("DateTime").contains(u"2015-04-05T14:30")
            True
            >>> t("DateTime").contains(u"2007-04-05T14:30 DROP TABLE users;")
            False
        """
        try:
            self.from_json(json_value)
            return True
        except Undefined:
            return False

    def from_json(self, json_value):
        """Convert JSON value to native value. Raises :exc:`Undefined` if
        *json_value* is not a member of this type.

        .. code-block:: python

            >>> t("DateTime").from_json(u"2015-04-05T14:30")
            datetime.datetime(2015, 4, 5, 14, 30)
        """
        if self.contains(json_value):
            return json_value
        else:
            raise Undefined()

    def to_json(self, native_value):
        """Convert valid native value to JSON value.

        .. code-block:: python

            >>> t("DateTime").to_json(datetime.datetime(2015, 4, 5, 14, 30))
            u"2015-04-05T14:30"


        """
        return native_value



class ConcreteType(Type):

    def __init__(self, t):
        self.t = t



class GenericType(Type):

    def __init__(self, t, param):
        self.t = t
        self.process_param(param)

    def process_param(self, param):
        self.param = param

    def contains(self, value):
        try:
            self.from_json(value)
            return True
        except Undefined:
            return False

    def from_json(self, value):
        return value

    def to_json(self, value):
        return value


class ArrayType(GenericType):

    def process_param(self, param):
        self.space = self.t(param)

    def from_json(self, value):

        if type(value) != list:
            raise Undefined()

        return map(self.space.from_json, value)

    def to_json(self, value):
        return map(self.space.to_json, value)


class MapType(GenericType):

    def process_param(self, param):
        self.space = self.t(param)

    def from_json(self, value):

        if type(value) != dict:
            raise Undefined()

        ret = {}
        for key, val in value.items():
            ret[key] = self.space.from_json(val)

        return ret

    def to_json(self, value):
        ret = {}
        for key, val in value.items():
            ret[key] = self.space.to_json(val)

        return ret


class StructType(GenericType):

    def process_param(self, param):
        expected = {'required', 'optional'}

        if type(param) != dict or set(param.keys()) != expected:
            raise Undefined()

        self.schemas = {}
        for kind in expected:
            if type(param[kind]) != dict:
                raise Undefined()

            for k, s in param[kind].items():
                self.schemas[k] = t(s)

        self.opt = set(param['optional'].keys())
        self.req = set(param['required'].keys())

        if not self.opt.isdisjoint(self.req):
            raise Undefined()

    def from_json(self, value):

        if type(value) != dict:
            raise Undefined()

        for k in self.req:
            if k not in value:
                raise Undefined()

        ret = {}
        for k, v in value.items():
            ret[k] = self.schemas[k].from_json(v)

        return ret

    def to_json(self, value):
        ret = {}
        for k, v in value.items():
            ret[k] = self.schemas[k].to_json(v)

        return ret


class JSONType(ConcreteType):
    def contains(self, value):
        return True


class IntegerType(ConcreteType):
    def contains(self, value):
        return type(value) in (int, long)


class FloatType(ConcreteType):
    def contains(self, value):
        return type(value) == float


class StringType(ConcreteType):
    def contains(self, value):
        return type(value) == unicode


class BooleanType(ConcreteType):
    def contains(self, value):
        return type(value) == bool


class DateTimeType(ConcreteType):

    def from_json(self, value):
        try:
            return isodate.parse_datetime(value)
        except (isodate.isoerror.ISO8601Error, Exception):
            raise Undefined()

    def to_json(self, value):
        return value.isoformat()


class SchemaType(ConcreteType):

    def contains(self, value):
        try:
            t(value)
            return True
        except Undefined:
            return False


class Draft00(object):
    types_concrete = {
        u"JSON": JSONType,
        u"Integer": IntegerType,
        u"Float": FloatType,
        u"String": StringType,
        u"Boolean": BooleanType,
        u"DateTime": DateTimeType,
        u"Schema": SchemaType
    }
    types_generic = {
        u"Array": ArrayType,
        u"Map": MapType,
        u"Struct": StructType
    }

    def t(self, schema):

        if schema in self.types_concrete.keys():
            return self.types_concrete[schema](t)
        elif type(schema) == dict and len(schema) == 1:
            (name, param) = schema.items()[0]
            if name in self.types_generic.keys():
                return self.types_generic[name](t, param)

        raise Undefined()


t = Draft00().t

