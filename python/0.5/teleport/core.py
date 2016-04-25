from __future__ import unicode_literals

from datetime import tzinfo, timedelta
from .libteleport import *


class UTC(tzinfo):
    """Why is this not in the standard library?
    """
    ZERO = timedelta(0)

    def utcoffset(self, dt):
        return self.ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return self.ZERO

    def __repr__(self):
        return '<UTC>'


utc = UTC()


class ValidationError(Exception):
    pass


J = teleport_J


def _is(haxe_enum, tag):
    return haxe_enum.tag == tag


def _get(haxe_enum):
    return haxe_enum.params[0]


def wrap_json(pythonic_json_value):
    if pythonic_json_value is None:
        return J.JNull
    c = type(pythonic_json_value)
    if c in (int, float):
        return J.JNumber(pythonic_json_value)
    elif c is str:
        return J.JString(pythonic_json_value)
    elif c is bool:
        return J.JBoolean(pythonic_json_value)
    elif c in (list, tuple, set):
        ret = []
        for i in pythonic_json_value:
            ret.append(wrap_json(i))
        return J.JArray(ret)
    elif c is dict:
        d = haxe_ds_StringMap()
        for k, v in pythonic_json_value.items():
            d.h[k] = wrap_json(v)
        return J.JObject(d)


def unwrap_json(haxe_json_value):
    t = haxe_json_value.tag
    if t is "JNull":
        return None
    p = _get(haxe_json_value)
    if t is ("JNumber", "JString", "JBoolean"):
        return p
    elif t is "JArray":
        ret = []
        for i in p:
            ret.append(unwrap_json(i))
        return ret
    elif t is "JObject":
        ret = {}
        for k, v in p:
            ret[k] = unwrap_json(v)
        return ret


class Teleport(teleport_Teleport):
    pass


class Type(object):

    def __init__(self, json_value):
        self.j = wrap_json(json_value)
        e = teleport_SchemaTools.schemaFromJsonValue(self.j)
        if _is(e, 'Right'):
            self.schema = _get(e)
        else:
            raise ValidationError(_get(e))

    def check(self, json_value):
        j = wrap_json(json_value)
        return Teleport().validate(self.schema, j)

    def from_json(self, json_value):
        j = wrap_json(json_value)
        e = Teleport().deserialize(self.schema, j)
        if _is(e, 'Right'):
            return _get(e)
        else:
            raise ValidationError("invalid schema")

    def to_json(self, native_value):
        pass


t = Type
