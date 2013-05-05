from unittest2 import TestCase

from copy import deepcopy

from teleport import *

array_schema = {
    "type": u"array",
    "items": {
        "type": u"boolean"
    }
}
struct_schema = {
    "type": u"struct",
    "fields": [
        required(u"foo", {"type": u"boolean"}),
        optional(u"bar", {"type": u"integer"})
    ]
}
deep_schema = {
    "type": u"array",
    "items": struct_schema
}
array_serializer = Schema().deserialize(array_schema)
struct_serializer = Schema().deserialize(struct_schema)
deep_serializer = Schema().deserialize(deep_schema)

class TestSchema(TestCase):

    def test_serialize_schema(self):
        self.assertEqual(array_schema, Schema().serialize(array_serializer))
        self.assertEqual(struct_schema, Schema().serialize(struct_serializer))
        self.assertEqual(deep_schema, Schema().serialize(deep_serializer))

    def test_serialize_unfamiliar_schema(self):
        with self.assertRaisesRegexp(KeyError, "Teleport is unfamiliar"):
            Schema().serialize("This is a string, not a serializer")

    def test_schema_subclass_delegation(self):
        self.assertTrue(isinstance(Schema().deserialize({"type": u"integer"}), Integer))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"float"}), Float))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"boolean"}), Boolean))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"string"}), String))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"binary"}), Binary))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"schema"}), Schema))
        self.assertTrue(isinstance(Schema().deserialize({"type": u"json"}), JSON))

    def test_schema_extra_parts(self):
        # struct with items
        s = deepcopy(array_schema)
        s["fields"] = struct_schema["fields"]
        with self.assertRaisesRegexp(ValidationError, "Unexpected fields"):
            Schema().deserialize(s)
        # array with fields
        s = deepcopy(struct_schema)
        s["items"] = array_schema["items"]
        with self.assertRaisesRegexp(ValidationError, "Unexpected fields"):
            Schema().deserialize(s)

    def test_schema_duplicate_fields(self):
        s = deepcopy(struct_schema)
        s["fields"][1]["name"] = u"foo"
        with self.assertRaisesRegexp(ValidationError, "Duplicate fields"):
            Schema().deserialize(s)

    def test_schema_not_struct(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid schema: True"):
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
        with self.assertRaisesRegexp(ValidationError, "Invalid float"):
            Float().deserialize(True)

    def test_serialize(self):
        self.assertEqual(Float().serialize(1.1), 1.1)


class TestInteger(TestCase):

    def test_deserialize(self):
        self.assertEqual(Integer().deserialize(1), 1)
        self.assertEqual(Integer().deserialize(1.0), 1)
        with self.assertRaisesRegexp(ValidationError, "Invalid integer"):
            Integer().deserialize(1.1)

    def test_serialize(self):
        self.assertEqual(Integer().serialize(1), 1)


class TestBoolean(TestCase):

    def test_deserialize(self):
        self.assertEqual(Boolean().deserialize(True), True)
        with self.assertRaisesRegexp(ValidationError, "Invalid boolean"):
            Boolean().deserialize(0)

    def test_serialize(self):
        self.assertEqual(Boolean().serialize(True), True)


class TestString(TestCase):

    def test_string_okay(self):
        self.assertEqual(String().deserialize(u"omg"), u"omg")

    def test_string_fail(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid string"):
            self.assertEqual(String().deserialize("omg"), u"omg")
        with self.assertRaisesRegexp(ValidationError, "Invalid string"):
            String().deserialize(0)

    def test_serialize(self):
        self.assertEqual(String().serialize(u"yo"), u"yo")


class TestBinary(TestCase):

    def test_deserialize(self):
        self.assertEqual(Binary().deserialize('YWJj'), "abc")
        self.assertEqual(Binary().deserialize(u'YWJj'), "abc")
        with self.assertRaisesRegexp(ValidationError, "Invalid base64"):
            # Will complain about incorrect padding
            Binary().deserialize("a")
        with self.assertRaisesRegexp(ValidationError, "Invalid binary"):
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
        with self.assertRaisesRegexp(ValidationError, "Invalid array"):
            array_serializer.deserialize(("no", "tuples",))
        with self.assertRaisesRegexp(ValidationError, "Invalid boolean"):
            array_serializer.deserialize([True, False, 1])


class TestStruct(TestCase):

    def test_deserialize(self):
        res = struct_serializer.deserialize({"foo": True, "bar": 2.0})
        self.assertEqual(res, {"foo": True, "bar": 2})
        res = struct_serializer.deserialize({"foo": True})
        self.assertEqual(res, {"foo": True})

    def test_deserialize_fail(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid struct"):
            struct_serializer.deserialize([])
        with self.assertRaisesRegexp(ValidationError, "Unexpected fields"):
            struct_serializer.deserialize({"foo": True, "barr": 2.0})
        with self.assertRaisesRegexp(ValidationError, "Missing fields"):
            struct_serializer.deserialize({"bar": 2})


