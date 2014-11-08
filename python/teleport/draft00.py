import isodate


class Undefined(Exception):
    pass


class Set(object):

    def __init__(self, f):
        self.f = f

    def __contains__(self, value):
        return self.f(value)


def is_datetime(value):
    try:
        isodate.parse_datetime(value)
        return True
    except (isodate.isoerror.ISO8601Error, Exception):
        return False


def is_schema(value):
    try:
        t(value)
        return True
    except Undefined:
        return False


class ArraySet(object):

    def __init__(self, param):
        self.space = t(param)

    def __contains__(self, value):

        if type(value) != list:
            return False

        for element in value:
            if element not in self.space:
                return False

        return True


class MapSet(object):

    def __init__(self, param):
        self.space = t(param)

    def __contains__(self, value):

        if type(value) != dict:
            return False

        for key, val in value.items():
            if val not in self.space:
                return False

        return True


class StructSet(object):

    def __init__(self, param):
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

    def __contains__(self, value):

        if type(value) != dict:
            return False

        for k in self.req:
            if k not in value:
                return False

        for k, v in value.items():
            if k not in self.schemas or v not in self.schemas[k]:
                return False

        return True


BUILTIN_CONCRETE = {
    u"JSON": Set(lambda _: True),
    u"Integer": Set(lambda value: type(value) in (int, long)),
    u"Float": Set(lambda value: type(value) == float),
    u"String": Set(lambda value: type(value) == unicode),
    u"Boolean": Set(lambda value: type(value) == bool),
    u"DateTime": Set(is_datetime),
    u"Schema": Set(is_schema)
}
BUILTIN_GENERIC = {
    u"Array": ArraySet,
    u"Map": MapSet,
    u"Struct": StructSet,
}


def t(schema):

    if schema in BUILTIN_CONCRETE.keys():
        return BUILTIN_CONCRETE[schema]
    elif type(schema) == dict and len(schema) == 1:
        (name, param) = schema.items()[0]
        if name in BUILTIN_GENERIC.keys():
            return BUILTIN_GENERIC[name](param)

    raise Undefined()























