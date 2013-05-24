from unittest2 import TestCase

from copy import deepcopy

from teleport import *

array_schema = {
    "type": u"Array",
    "param": {
        "type": u"Boolean"
    }
}
struct_schema = {
    "type": u"Struct",
    "param": {
        "map": {
            u"foo": required({"type": u"Boolean"}),
            u"bar": optional({"type": u"Integer"})
        },
        "order": [u"foo", u"bar"]
    }
}
map_schema = {
    "type": u"Map",
    "param": {"type": "Boolean"}
}
ordered_map_schema = {
    "type": u"OrderedMap",
    "param": {"type": "Boolean"}
}
deep_schema = {
    "type": u"Array",
    "param": struct_schema
}
array_serializer = Schema().deserialize(array_schema)
struct_serializer = Schema().deserialize(struct_schema)
deep_serializer = Schema().deserialize(deep_schema)
map_serializer = Schema().deserialize(map_schema)
ordered_map_serializer = Schema().deserialize(ordered_map_schema)

class TestSchema(TestCase):

    def test_serialize_schema(self):
        self.assertEqual(array_schema, Schema().serialize(array_serializer))
        self.assertEqual(struct_schema, Schema().serialize(struct_serializer))
        self.assertEqual(deep_schema, Schema().serialize(deep_serializer))

    def test_schema_subclass_delegation(self):
        self.assertTrue(isinstance(Schema().deserialize({"type": u"Integer"}), Integer))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"Float"}), Float))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"Boolean"}), Boolean))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"String"}), String))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"Binary"}), Binary))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"Schema"}), Schema))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"JSON"}), JSON))

    def test_schema_duplicate_fields(self):
        s = deepcopy(struct_schema)
        s["param"]["order"].append("blah")
        with self.assertRaisesRegexp(ValidationError, "Invalid OrderedMap"):
            Schema().deserialize(s)

    def test_schema_not_struct(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid Schema: True"):
            Schema().deserialize(True)

    def test_schema_unknown_type(self):
        with self.assertRaisesRegexp(ValidationError, "Unknown type"):
            Schema().deserialize({"type": "number"})

    def test_deep_schema_validation_stack(self):
        # Test Python representatioon
        with self.assertRaisesRegexp(ValidationError, "\[0\]\[u'bar'\]"):
            deep_serializer.deserialize([{"foo": True, "bar": False}])


class TestFloat(TestCase):

    def test_deserialize(self):
        self.assertEqual(Float().deserialize(1), 1.0)
        self.assertEqual(Float().deserialize(1.0), 1.0)
        with self.assertRaisesRegexp(ValidationError, "Invalid Float"):
            Float().deserialize(True)

    def test_serialize(self):
        self.assertEqual(Float().serialize(1.1), 1.1)


class TestInteger(TestCase):

    def test_deserialize(self):
        self.assertEqual(Integer().deserialize(1), 1)
        self.assertEqual(Integer().deserialize(1.0), 1)
        with self.assertRaisesRegexp(ValidationError, "Invalid Integer"):
            Integer().deserialize(1.1)

    def test_serialize(self):
        self.assertEqual(Integer().serialize(1), 1)


class TestBoolean(TestCase):

    def test_deserialize(self):
        self.assertEqual(Boolean().deserialize(True), True)
        with self.assertRaisesRegexp(ValidationError, "Invalid Boolean"):
            Boolean().deserialize(0)

    def test_serialize(self):
        self.assertEqual(Boolean().serialize(True), True)


class TestString(TestCase):

    def test_string_okay(self):
        self.assertEqual(String().deserialize(u"omg"), u"omg")
        self.assertEqual(String().deserialize("omg"), u"omg")

    def test_string_fail(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid String"):
            String().deserialize(0)
        with self.assertRaisesRegexp(UnicodeDecodeValidationError, "invalid start byte"):
            String().deserialize("\xff")

    def test_serialize(self):
        self.assertEqual(String().serialize(u"yo"), u"yo")


class TestBinary(TestCase):

    def test_deserialize(self):
        self.assertEqual(Binary().deserialize('YWJj'), "abc")
        self.assertEqual(Binary().deserialize(u'YWJj'), "abc")
        with self.assertRaisesRegexp(ValidationError, "Invalid base64"):
            # Will complain about incorrect padding
            Binary().deserialize("a")
        with self.assertRaisesRegexp(ValidationError, "Invalid Binary"):
            Binary().deserialize(1)

    def test_serialize(self):
        self.assertEqual(Binary().serialize("abc"), "YWJj")


class TestJSON(TestCase):

    def test_deserialize(self):
        self.assertTrue(isinstance(JSON().deserialize("A string?"), Box))
        self.assertEqual(JSON().deserialize('ABC').datum, "ABC")

    def test_serialize(self):
        self.assertEqual(JSON().serialize(Box("abc")), "abc")


class TestArray(TestCase):

    def test_deserialize(self):
        self.assertEqual(array_serializer.deserialize([True, False]), [True, False])
        with self.assertRaisesRegexp(ValidationError, "Invalid Array"):
            array_serializer.deserialize(("no", "tuples",))
        with self.assertRaisesRegexp(ValidationError, "Invalid Boolean"):
            array_serializer.deserialize([True, False, 1])


class TestMap(TestCase):

    def test_deserialize_and_serialize(self):
        m = {
            u"cool": True,
            u"hip": False,
            u"groovy": True
        }
        self.assertEqual(map_serializer.deserialize(m), m)
        self.assertEqual(map_serializer.serialize(m), m)
        with self.assertRaisesRegexp(ValidationError, "Invalid Map"):
            map_serializer.deserialize([True, False])
        with self.assertRaisesRegexp(ValidationError, "must be unicode"):
            map_serializer.deserialize({"nope": False})


class TestOrderedMap(TestCase):

    def test_deserialize_and_serialize(self):
        m = {
            "map": {
                u"cool": True,
                u"hip": False,
                u"groovy": True
            },
            "order": [u"cool", u"groovy", u"hip"]
        }
        self.assertEqual(ordered_map_serializer.deserialize(m), m)
        self.assertEqual(ordered_map_serializer.serialize(m), m)
        with self.assertRaisesRegexp(ValidationError, "Invalid OrderedMap"):
            m2 = deepcopy(m)
            m2["order"].append(u"cool")
            ordered_map_serializer.deserialize(m2)
        with self.assertRaisesRegexp(ValidationError, "Invalid OrderedMap"):
            m2 = deepcopy(m)
            m2["order"] = [u"cool", u"groovy", u"kewl"]
            ordered_map_serializer.deserialize(m2)


class TestStruct(TestCase):

    def test_deserialize(self):
        res = struct_serializer.deserialize({"foo": True, "bar": 2.0})
        self.assertEqual(res, {"foo": True, "bar": 2})
        res = struct_serializer.deserialize({"foo": True})
        self.assertEqual(res, {"foo": True})

    def test_deserialize_fail(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid Struct"):
            struct_serializer.deserialize([])
        with self.assertRaisesRegexp(ValidationError, "Unexpected fields"):
            struct_serializer.deserialize({"foo": True, "barr": 2.0})
        with self.assertRaisesRegexp(ValidationError, "Missing fields"):
            struct_serializer.deserialize({"bar": 2})


class Suit(object):

    def deserialize(self, datum):
        if datum not in ["hearts", "spades", "clubs", "diamonds"]:
            raise ValidationError("Invalid Suit", datum)
        return datum

    def serialize(self, datum):
        return datum


class TestSuit(TestCase):

    def test_deserialize(self):
        suits = ["hearts", "clubs", "clubs"]
        self.assertEqual(Array(Suit()).deserialize(suits), suits)
        with self.assertRaisesRegexp(ValidationError, "Invalid Suit"):
            suits = ["hearts", "clubs", "clubz"]
            self.assertEqual(Array(Suit()).deserialize(suits), suits)


class AllSuits(TypeMap):

    def __getitem__(self, name):
        if name == "Array":
            return Array
        elif name == "suit":
            return Suit
        else:
            raise KeyError()


class TestTypeMap(TestCase):

    def test_custom_type_map_okay(self):

        with AllSuits():
            self.assertEqual(Schema().deserialize({
                "type": "suit"
            }).__class__, Suit)
            self.assertEqual(Schema().deserialize({
                "type": "Array",
                "param": {"type": "suit"}
            }).__class__, Array)

    def test_custom_type_map_fail(self):

        Schema().deserialize({"type": "Integer"})

        with self.assertRaises(UnknownTypeValidationError):
            with AllSuits():
                Schema().deserialize({"type": "Integer"})

    def test_wsgi_middleware(self):
        # Inspired by https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/testapp.py
        from werkzeug.wrappers import BaseResponse
        from werkzeug.test import Client

        def test_app(environ, start_response):
            # Needs to access AllSuits
            S = Schema().deserialize({"type": "suit"})
            response = BaseResponse(S.__class__.__name__, mimetype="text/plain")
            return response(environ, start_response)

        test_app = AllSuits().middleware(test_app)

        c = Client(test_app, BaseResponse)
        resp = c.get('/')

        self.assertEqual(resp.data, "Suit")

