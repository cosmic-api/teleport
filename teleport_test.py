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
array_serializer = Schema.from_json(array_schema)
struct_serializer = Schema.from_json(struct_schema)
deep_serializer = Schema.from_json(deep_schema)
map_serializer = Schema.from_json(map_schema)
ordered_map_serializer = Schema.from_json(ordered_map_schema)

class TestSchema(TestCase):

    def test_to_json_schema(self):
        self.assertEqual(array_schema, Schema.to_json(array_serializer))
        self.assertEqual(struct_schema, Schema.to_json(struct_serializer))
        self.assertEqual(deep_schema, Schema.to_json(deep_serializer))

    def test_schema_subclass_delegation(self):
        self.assertEqual(Schema.from_json({"type": u"Integer"}), Integer)
        self.assertEqual(Schema.from_json({"type": u"Float"}), Float)
        self.assertEqual(Schema.from_json({"type": u"Boolean"}), Boolean)
        self.assertEqual(Schema.from_json({"type": u"String"}), String)
        self.assertEqual(Schema.from_json({"type": u"Binary"}), Binary)
        self.assertEqual(Schema.from_json({"type": u"Schema"}), Schema)
        self.assertEqual(Schema.from_json({"type": u"JSON"}), JSON)

    def test_schema_duplicate_fields(self):
        s = deepcopy(struct_schema)
        s["param"]["order"].append("blah")
        with self.assertRaisesRegexp(ValidationError, "Invalid OrderedMap"):
            Schema.from_json(s)

    def test_schema_not_struct(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid Schema: True"):
            Schema.from_json(True)

    def test_schema_unknown_type(self):
        with self.assertRaisesRegexp(ValidationError, "Unknown type"):
            Schema.from_json({"type": "number"})

    def test_deep_schema_validation_stack(self):
        # Test Python representatioon
        with self.assertRaisesRegexp(ValidationError, "\[0\]\[u'bar'\]"):
            deep_serializer.from_json([{"foo": True, "bar": False}])


class TestFloat(TestCase):

    def test_from_json(self):
        self.assertEqual(Float().from_json(1), 1.0)
        self.assertEqual(Float().from_json(1.0), 1.0)
        with self.assertRaisesRegexp(ValidationError, "Invalid Float"):
            Float().from_json(True)

    def test_to_json(self):
        self.assertEqual(Float().to_json(1.1), 1.1)


class TestInteger(TestCase):

    def test_from_json(self):
        self.assertEqual(Integer().from_json(1), 1)
        self.assertEqual(Integer().from_json(1.0), 1)
        with self.assertRaisesRegexp(ValidationError, "Invalid Integer"):
            Integer().from_json(1.1)

    def test_to_json(self):
        self.assertEqual(Integer().to_json(1), 1)


class TestBoolean(TestCase):

    def test_from_json(self):
        self.assertEqual(Boolean().from_json(True), True)
        with self.assertRaisesRegexp(ValidationError, "Invalid Boolean"):
            Boolean().from_json(0)

    def test_to_json(self):
        self.assertEqual(Boolean().to_json(True), True)


class TestString(TestCase):

    def test_string_okay(self):
        self.assertEqual(String().from_json(u"omg"), u"omg")
        self.assertEqual(String().from_json("omg"), u"omg")

    def test_string_fail(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid String"):
            String().from_json(0)
        with self.assertRaisesRegexp(UnicodeDecodeValidationError, "invalid start byte"):
            String().from_json("\xff")

    def test_to_json(self):
        self.assertEqual(String().to_json(u"yo"), u"yo")


class TestBinary(TestCase):

    def test_from_json(self):
        self.assertEqual(Binary().from_json('YWJj'), "abc")
        self.assertEqual(Binary().from_json(u'YWJj'), "abc")
        with self.assertRaisesRegexp(ValidationError, "Invalid base64"):
            # Will complain about incorrect padding
            Binary().from_json("a")
        with self.assertRaisesRegexp(ValidationError, "Invalid Binary"):
            Binary().from_json(1)

    def test_to_json(self):
        self.assertEqual(Binary().to_json("abc"), "YWJj")


class TestJSON(TestCase):

    def test_from_json(self):
        self.assertTrue(isinstance(JSON().from_json("A string?"), Box))
        self.assertEqual(JSON().from_json('ABC').datum, "ABC")

    def test_to_json(self):
        self.assertEqual(JSON().to_json(Box("abc")), "abc")


class TestArray(TestCase):

    def test_from_json(self):
        self.assertEqual(array_serializer.from_json([True, False]), [True, False])
        with self.assertRaisesRegexp(ValidationError, "Invalid Array"):
            array_serializer.from_json(("no", "tuples",))
        with self.assertRaisesRegexp(ValidationError, "Invalid Boolean"):
            array_serializer.from_json([True, False, 1])


class TestMap(TestCase):

    def test_from_json_and_to_json(self):
        m = {
            u"cool": True,
            u"hip": False,
            u"groovy": True
        }
        self.assertEqual(map_serializer.from_json(m), m)
        self.assertEqual(map_serializer.to_json(m), m)
        with self.assertRaisesRegexp(ValidationError, "Invalid Map"):
            map_serializer.from_json([True, False])
        with self.assertRaisesRegexp(ValidationError, "must be unicode"):
            map_serializer.from_json({"nope": False})


class TestOrderedMap(TestCase):

    def test_from_json_and_to_json(self):
        m = {
            "map": {
                u"cool": True,
                u"hip": False,
                u"groovy": True
            },
            "order": [u"cool", u"groovy", u"hip"]
        }
        self.assertEqual(ordered_map_serializer.from_json(m), m)
        self.assertEqual(ordered_map_serializer.to_json(m), m)
        with self.assertRaisesRegexp(ValidationError, "Invalid OrderedMap"):
            m2 = deepcopy(m)
            m2["order"].append(u"cool")
            ordered_map_serializer.from_json(m2)
        with self.assertRaisesRegexp(ValidationError, "Invalid OrderedMap"):
            m2 = deepcopy(m)
            m2["order"] = [u"cool", u"groovy", u"kewl"]
            ordered_map_serializer.from_json(m2)


class TestStruct(TestCase):

    def test_from_json(self):
        res = struct_serializer.from_json({"foo": True, "bar": 2.0})
        self.assertEqual(res, {"foo": True, "bar": 2})
        res = struct_serializer.from_json({"foo": True})
        self.assertEqual(res, {"foo": True})

    def test_from_json_fail(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid Struct"):
            struct_serializer.from_json([])
        with self.assertRaisesRegexp(ValidationError, "Unexpected fields"):
            struct_serializer.from_json({"foo": True, "barr": 2.0})
        with self.assertRaisesRegexp(ValidationError, "Missing fields"):
            struct_serializer.from_json({"bar": 2})


class Suit(object):

    @staticmethod
    def from_json(datum):
        if datum not in ["hearts", "spades", "clubs", "diamonds"]:
            raise ValidationError("Invalid Suit", datum)
        return datum

    @staticmethod
    def to_json(datum):
        return datum


class TestSuit(TestCase):

    def test_from_json(self):
        suits = ["hearts", "clubs", "clubs"]
        self.assertEqual(Array(Suit).from_json(suits), suits)
        with self.assertRaisesRegexp(ValidationError, "Invalid Suit"):
            suits = ["hearts", "clubs", "clubz"]
            self.assertEqual(Array(Suit).from_json(suits), suits)


class AllSuits(TypeMap):

    def __getitem__(self, name):
        if name == "Array":
            return BUILTIN_TYPES["Array"]
        elif name == "suit":
            return (Suit, None,)
        else:
            raise KeyError()


class TestTypeMap(TestCase):

    def test_custom_type_map_okay(self):

        with AllSuits():
            self.assertEqual(Schema.from_json({
                "type": "suit"
            }), Suit)
            self.assertEqual(Schema.from_json({
                "type": "Array",
                "param": {"type": "suit"}
            }).__class__, Array)

    def test_custom_type_map_fail(self):

        Schema.from_json({"type": "Integer"})

        with self.assertRaises(UnknownTypeValidationError):
            with AllSuits():
                Schema.from_json({"type": "Integer"})

    def test_wsgi_middleware(self):
        # Inspired by https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/testapp.py
        from werkzeug.wrappers import BaseResponse
        from werkzeug.test import Client

        def test_app(environ, start_response):
            # Needs to access AllSuits
            S = Schema.from_json({"type": "suit"})
            response = BaseResponse(S.__name__, mimetype="text/plain")
            return response(environ, start_response)

        test_app = AllSuits().middleware(test_app)

        c = Client(test_app, BaseResponse)
        resp = c.get('/')

        self.assertEqual(resp.data, "Suit")

