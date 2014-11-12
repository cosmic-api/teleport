from unittest2 import TestCase
from datetime import datetime

from teleport.draft00 import t



class T(object):
    pairs_exact = []
    pairs_inexact = []
    undefined = []

    def test_from_json(self):
        for pair in self.pairs_exact:
            self.assertIs(t(self.schema).from_json(pair[0]), pair[1])
        for pair in self.pairs_inexact:
            self.assertEqual(t(self.schema).from_json(pair[0]), pair[1])

    def test_to_json(self):
        for pair in self.pairs_exact:
            self.assertIs(t(self.schema).to_json(pair[1]), pair[0])
        for pair in self.pairs_inexact:
            self.assertEqual(t(self.schema).to_json(pair[1]), pair[0])




class IntegerTest(T, TestCase):
    schema = "Integer"
    pairs_exact = [(1, 1), (1L, 1L)]


class FloatTest(T, TestCase):
    schema = "Float"
    pairs_exact = [(0.1, 0.1), (1e10, 1e10)]


class StringTest(T, TestCase):
    schema = "String"
    pairs_exact = [(u"lol", u"lol")]


class BooleanTest(T, TestCase):
    schema = "Boolean"
    pairs_exact = [(True, True), (False, False)]


class DateTimeTest(T, TestCase):
    schema = "DateTime"
    pairs_inexact = [('2013-10-18T01:58:24.904349', datetime(2013, 10, 18, 1, 58, 24, 904349))]


class JSONTest(T, TestCase):
    schema = "JSON"
    o = object()
    pairs_exact = [(o, o)]


class SchemaTest(T, TestCase):
    schema = "Schema"
    pairs_exact = [(u'Integer', u'Integer')]


