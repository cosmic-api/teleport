import isodate


class Undefined(Exception):
    pass


class Type(object):

    def __init__(self, t):
        self.t = t

    def __contains__(self, value):
        try:
            self.from_json(value)
            return True
        except Undefined:
            return False

    def from_json(self, value):
        if value in self:
            return value
        else:
            raise Undefined()

    def to_json(self, value):
        return value


class ConcreteType(Type):
    pass


class GenericType(Type):

    def __init__(self, t, param):
        self.t = t
        self.process_param(param)

    def process_param(self, param):
        self.param = param

    def __contains__(self, value):
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
    def __contains__(self, value):
        return True


class IntegerType(ConcreteType):
    def __contains__(self, value):
        return type(value) in (int, long)


class FloatType(ConcreteType):
    def __contains__(self, value):
        return type(value) == float


class StringType(ConcreteType):
    def __contains__(self, value):
        return type(value) == unicode


class BooleanType(ConcreteType):
    def __contains__(self, value):
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

    def __contains__(self, value):
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

