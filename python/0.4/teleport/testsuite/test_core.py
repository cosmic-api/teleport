from unittest2 import TestCase
from datetime import datetime

from teleport import t, utc, Undefined, ValidationError
from teleport.compat import PY2


class T(object):
    pairs = []
    undefined = []

    def test_from_json(self):
        for pair in self.pairs:
            self.assertEqual(t(self.schema).from_json(pair[0]), pair[1])

    def test_to_json(self):
        for pair in self.pairs:
            self.assertEqual(t(self.schema).to_json(pair[1]), pair[0])


ds = '2013-10-18T01:58:24.904349Z'
dn = datetime(2013, 10, 18, 1, 58, 24, 904349, tzinfo=utc)


class IntegerTest(T, TestCase):
    schema = "Integer"
    pairs = [(1, 1)]

    if PY2:
        pairs.append((long(1), long(1)))




class DecimalTest(T, TestCase):
    schema = "Decimal"
    pairs = [(0.1, 0.1), (1e10, 1e10)]


class StringTest(T, TestCase):
    schema = "String"
    pairs = [(u"lol", u"lol")]


class BooleanTest(T, TestCase):
    schema = "Boolean"
    pairs = [(True, True), (False, False)]


class DateTimeTest(T, TestCase):
    schema = "DateTime"
    pairs = [(ds, dn)]


class JSONTest(T, TestCase):
    schema = "JSON"
    o = object()
    pairs = [(o, o)]


class SchemaTest(T, TestCase):
    schema = "Schema"
    pairs = [(u'Integer', u'Integer')]


class ArrayTest(T, TestCase):
    schema = {"Array": "DateTime"}
    pairs = [([ds, ds], [dn, dn])]


class MapTest(T, TestCase):
    schema = {"Map": "DateTime"}
    pairs = [({"a": ds, "b": ds}, {"a": dn, "b": dn})]


class StructTest(T, TestCase):
    schema = {"Struct": {
        "required": {"a": "DateTime"},
        "optional": {"b": "Integer"}}}
    pairs = [({"a": ds, "b": 1}, {"a": dn, "b": 1}), ({"a": ds}, {"a": dn})]




class ErrorTest(TestCase):

    def setUp(self):
        self.t = t({"Struct": {
            "optional": {},
            "required": {
                "name": "String",
                "tags": {"Array": "String"}}}})

    def test_errors(self):

        try:
            self.t.from_json({
                "tags": ["a", True],
                "lol": 1
            })
        except ValidationError as m:
            pass
            """
            import pdb; pdb.set_trace()
            self.assertEqual(m.to_json(), [
                {"error": ["MissingField", "name"], "pointer": []},
                {"error": ["UnexpectedField", "lol"], "pointer": []},
                {"error": [], "pointer": ["tags", 1]}
            ])
            self.assertEqual([OrderedDict([(u'message', u'Missing field: "name"'), (u'pointer', [])]), OrderedDict([(u'message', u'Unexpected field: "lol"'), (u'pointer', [])]), OrderedDict([(u'message', u'Not a string'), (u'pointer', ['tags', 1])])])
            """
