import re

from unittest2 import TestCase
from datetime import datetime

from teleport.draft00 import t, Teleport, ConcreteType, GenericType



class T(object):
    pairs = []
    undefined = []

    def test_from_json(self):
        for pair in self.pairs:
            self.assertEqual(t(self.schema).from_json(pair[0]), pair[1])

    def test_to_json(self):
        for pair in self.pairs:
            self.assertEqual(t(self.schema).to_json(pair[1]), pair[0])


ds = '2013-10-18T01:58:24.904349'
dn = datetime(2013, 10, 18, 1, 58, 24, 904349)


class IntegerTest(T, TestCase):
    schema = "Integer"
    pairs = [(1, 1), (1L, 1L)]


class FloatTest(T, TestCase):
    schema = "Float"
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



class ExtendingTest(TestCase):

    def test_extend(self):
        t = Teleport()

        @t.register("Color")
        class ColorType(ConcreteType):

            def contains(self, value):
                if not t("String").contains(value):
                    return False
                return re.compile('^#[0-9a-f]{6}$').match(value) is not None

        self.assertTrue(t("Color").contains('#ffffff'))
        self.assertFalse(t("Color").contains('yellow'))
        self.assertTrue(t({"Array": "Color"}).contains(['#ffffff', '#000000']))

