from unittest2 import TestCase, TestSuite

from copy import deepcopy
from datetime import datetime

from teleport import *
import teleport.types2

array_schema = {u"Array": u"Boolean"}

struct_schema = {
    "Struct": [
        {
            "name": "foo",
            "required": True,
            "schema": "Boolean",
            "doc": "Never gonna give you up"
        },
        {
            "name": "bar",
            "required": False,
            "schema": "Integer"
        }
    ]
}
map_schema = {
    "Map": "Boolean"
}
ordered_map_schema = {
    "OrderedMap": "Boolean"
}
deep_schema = {
    "Array": struct_schema
}
array_serializer = teleport.types2.Schema.from_json(array_schema)
struct_serializer = Schema().from_json(struct_schema)
deep_serializer = Schema().from_json(deep_schema)
map_serializer = Schema().from_json(map_schema)
ordered_map_serializer = Schema().from_json(ordered_map_schema)

class TestSchema(TestCase):

    def test_to_json_schema(self):
        self.assertEqual(array_schema, teleport.types2.Schema.to_json(array_serializer))
        self.assertEqual(struct_schema, Schema().to_json(struct_serializer))
        self.assertEqual(deep_schema, Schema().to_json(deep_serializer))
        struct_s = Struct([
            required("foo", Boolean(), u"Never gonna give you up"),
            optional("bar", Integer())
        ])
        self.assertEqual(Schema().to_json(struct_s), struct_schema)

    def _test_schema_subclass_delegation(self):
        self.assertEqual(teleport.types2.Schema.from_json("Integer"), teleport.types2.Integer)
        self.assertEqual(teleport.types2.Schema.from_json("Float"), teleport.types2.Float)
        self.assertEqual(teleport.types2.Schema.from_json("String"), teleport.types2.String)
        self.assertEqual(teleport.types2.Schema.from_json("Boolean"), teleport.types2.Boolean)
        self.assertEqual(teleport.types2.Schema.from_json("DateTime"), teleport.types2.DateTime)
        self.assertEqual(teleport.types2.Schema.from_json("Binary"), teleport.types2.Binary)
        self.assertEqual(teleport.types2.Schema.from_json("Schema"), teleport.types2.Schema)
        self.assertEqual(teleport.types2.Schema.from_json("JSON"), teleport.types2.JSON)

    def test_schema_duplicate_fields(self):
        s = deepcopy(struct_schema)
        s["Struct"].append(s["Struct"][0])
        with self.assertRaisesRegexp(ValidationError, "Names cannot repeat"):
            Schema().from_json(s)

    def test_schema_not_struct(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid Schema: True"):
            Schema().from_json(True)

    def test_schema_unknown_type(self):
        with self.assertRaisesRegexp(ValidationError, "Unknown type"):
            Schema().from_json({"type": "number"})

    def test_deep_schema_validation_stack(self):
        # Test Python representatioon
        with self.assertRaisesRegexp(ValidationError, "\[0\]\[u'bar'\]"):
            deep_serializer.from_json([{"foo": True, "bar": False}])

    def test_wrapper_schema_validation_error(self):
        s = OrderedMap(Array(Integer()))
        with self.assertRaisesRegexp(ValidationError, "\[u'foo'\]\[1\]"):
            s.from_json({
                u"map": {
                    u"foo": [1, 2.1]
                },
                u"order": [u"foo"]
            })

    def test_unexpected_param(self):
        with self.assertRaisesRegexp(ValidationError, "Unexpected param"):
            Schema().from_json({"Integer": 1})

    def test_missing_param(self):
        with self.assertRaisesRegexp(ValidationError, "Missing param"):
            Schema().from_json("Struct")



class TestFloat(TestCase):

    def test_from_json(self):
        self.assertEqual(teleport.types2.Float.from_json(1), 1.0)
        self.assertEqual(teleport.types2.Float.from_json(1.0), 1.0)
        with self.assertRaisesRegexp(teleport.types2.ValidationError, "Invalid Float"):
            teleport.types2.Float.from_json(True)

    def test_to_json(self):
        self.assertEqual(teleport.types2.Float.to_json(1.1), 1.1)


class TestInteger(TestCase):

    def test_from_json(self):
        self.assertEqual(teleport.types2.Integer.from_json(1), 1)
        self.assertEqual(teleport.types2.Integer.from_json(1.0), 1)
        with self.assertRaisesRegexp(teleport.types2.ValidationError, "Invalid Integer"):
            teleport.types2.Integer.from_json(1.1)

    def test_to_json(self):
        self.assertEqual(teleport.types2.Integer.to_json(1), 1)


class TestBoolean(TestCase):

    def test_from_json(self):
        self.assertEqual(teleport.types2.Boolean.from_json(True), True)
        with self.assertRaisesRegexp(teleport.types2.ValidationError, "Invalid Boolean"):
            teleport.types2.Boolean.from_json(0)

    def test_to_json(self):
        self.assertEqual(teleport.types2.Boolean.to_json(True), True)


class TestString(TestCase):

    def test_string_okay(self):
        self.assertEqual(teleport.types2.String.from_json(u"omg"), u"omg")
        self.assertEqual(teleport.types2.String.from_json("omg"), u"omg")

    def test_string_fail(self):
        with self.assertRaisesRegexp(teleport.types2.ValidationError, "Invalid String"):
            teleport.types2.String.from_json(0)
        with self.assertRaisesRegexp(teleport.types2.UnicodeDecodeValidationError, "invalid start byte"):
            teleport.types2.String.from_json("\xff")

    def test_to_json(self):
        self.assertEqual(teleport.types2.String.to_json(u"yo"), u"yo")


class TestBinary(TestCase):

    def test_from_json(self):
        self.assertEqual(teleport.types2.Binary.from_json('YWJj'), "abc")
        self.assertEqual(teleport.types2.Binary.from_json(u'YWJj'), "abc")
        with self.assertRaisesRegexp(teleport.types2.ValidationError, "Invalid base64"):
            # Will complain about incorrect padding
            teleport.types2.Binary.from_json("a")
        with self.assertRaisesRegexp(teleport.types2.ValidationError, "Invalid Binary"):
            teleport.types2.Binary.from_json(1)

    def test_to_json(self):
        self.assertEqual(teleport.types2.Binary.to_json("abc"), "YWJj")


class TestJSON(TestCase):

    def test_from_json(self):
        self.assertTrue(isinstance(teleport.types2.JSON.from_json("A string?"), teleport.types2.Box))
        self.assertEqual(teleport.types2.JSON.from_json('ABC').datum, "ABC")

    def test_to_json(self):
        self.assertEqual(teleport.types2.JSON.to_json(Box("abc")), "abc")


class TestDateTime(TestCase):

    def test_from_json(self):
        self.assertTrue(isinstance(teleport.types2.DateTime.from_json('2013-10-04T13:05:25.354952'), datetime))
        self.assertEqual(teleport.types2.DateTime.from_json('2013-10-04T13:05:25.354952'), datetime(2013, 10, 4, 13, 5, 25, 354952))
        # Separator must be T!
        with self.assertRaises(teleport.types2.ValidationError):
            teleport.types2.DateTime.from_json('2013-10-04 13:05:25.354952')

    def test_to_json(self):
        self.assertEqual(teleport.types2.DateTime.to_json(datetime(2013, 10, 4, 13, 5, 25, 354952)), '2013-10-04T13:05:25.354952')


class TestArray(TestCase):

    def test_from_json(self):
        self.assertEqual(array_serializer.from_json([True, False]), [True, False])
        with self.assertRaisesRegexp(teleport.types2.ValidationError, "Invalid Array"):
            array_serializer.from_json(("no", "tuples",))
        with self.assertRaisesRegexp(teleport.types2.ValidationError, "Invalid Boolean"):
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
        with self.assertRaisesRegexp(ValidationError, "Expecting JSON object"):
            map_serializer.from_json([True, False])
        with self.assertRaisesRegexp(ValidationError, "must be unicode"):
            map_serializer.from_json({"nope": False})
        with self.assertRaisesRegexp(ValidationError, "Invalid Boolean"):
            map_serializer.from_json({u"cool": 0})


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
        md = OrderedDict([
            (u"cool", True,),
            (u"groovy", True,),
            (u"hip", False,)
        ])
        self.assertEqual(ordered_map_serializer.from_json(m), md)
        self.assertEqual(ordered_map_serializer.to_json(md), m)
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
        with self.assertRaisesRegexp(ValidationError, "Expecting JSON object"):
            struct_serializer.from_json([])
        with self.assertRaisesRegexp(ValidationError, "Unexpected fields"):
            struct_serializer.from_json({"foo": True, "barr": 2.0})
        with self.assertRaisesRegexp(ValidationError, "Missing fields"):
            struct_serializer.from_json({"bar": 2})

    def test_to_json(self):
        res = struct_serializer.to_json({"foo": True})
        self.assertEqual(res, {"foo": True})
        res = struct_serializer.to_json({"foo": True, "bar": None})
        self.assertEqual(res, {"foo": True})


"""

class Suit(BasicWrapper):
    schema = String

    @staticmethod
    def assemble(datum):
        if datum not in ["hearts", "spades", "clubs", "diamonds"]:
            raise ValidationError("Invalid Suit", datum)
        return datum

class SuitArray(BasicWrapper):
    schema = Array(Suit)


class TestSuits(TestCase):

    def test_from_json(self):
        suits = ["hearts", "clubs", "clubs"]
        self.assertEqual(SuitArray.from_json(suits), suits)
        with self.assertRaisesRegexp(ValidationError, "Invalid Suit"):
            suits = ["hearts", "clubs", "clubz"]
            self.assertEqual(SuitArray.from_json(suits), suits)

    def test_to_json(self):
        self.assertEqual(Suit.to_json(u"hearts"), u"hearts")

def getter(t):
    if t == "Suit":
        return Suit
    raise UnknownTypeValidationError(t)

suit_types = standard_types(getter, include=["Array", "Schema"])

class TestTypeMap(TestCase):

    def test_custom_type_map_okay(self):

        Schema = suit_types["Schema"]
        Array = suit_types["Array"]

        self.assertEqual(Schema.from_json("Suit"), Suit)
        self.assertEqual(Schema.from_json({"Array": "Suit"}).__class__, Array)

    def test_custom_type_map_fail(self):

        Schema = suit_types["Schema"]
        with self.assertRaises(UnknownTypeValidationError):
            Schema.from_json("Integer")

"""

def suite():
    s = TestSuite()

