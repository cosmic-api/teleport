from unittest2 import TestCase

from copy import deepcopy

from teleport import *

array_schema = {
    "type": "array",
    "items": {
        "type": "boolean"
    }
}
object_schema = {
    "type": "object",
    "properties": [
        {
            "name": "foo",
            "required": True,
            "schema": {"type": "boolean"}
        },
        {
            "name": "bar",
            "required": False,
            "schema": {"type": "integer"}
        }
    ]
}
deep_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": [
            {
                "name": "foo",
                "required": True,
                "schema": {"type": "boolean"}
            },
            {
                "name": "bar",
                "required": False,
                "schema": {"type": "integer"}
            }
        ]
    }
}
array_normalizer = Schema.normalize(array_schema)
object_normalizer = Schema.normalize(object_schema)
deep_normalizer = Schema.normalize(deep_schema)

class TestSchema(TestCase):

    def test_serialize_schema(self):
        self.assertEqual(deep_schema, deep_normalizer.serialize())

    def test_schema_subclass_delegation(self):
        self.assertTrue(isinstance(Schema.normalize({"type": "integer"}), IntegerSchema))
        self.assertTrue(isinstance(Schema.normalize({"type": "float"}), FloatSchema))
        self.assertTrue(isinstance(Schema.normalize({"type": "boolean"}), BooleanSchema))
        self.assertTrue(isinstance(Schema.normalize({"type": "string"}), StringSchema))
        self.assertTrue(isinstance(Schema.normalize({"type": "binary"}), BinarySchema))
        self.assertTrue(isinstance(Schema.normalize({"type": "json"}), JSONDataSchema))
        self.assertTrue(isinstance(Schema.normalize({"type": "schema"}), SchemaSchema))

    def test_schema_subclass_wrong_type(self):
        with self.assertRaisesRegexp(ValidationError, "expects type=string"):
            StringSchema.normalize({"type": "str"})

    def test_schema_missing_parts(self):
        # Forgot items
        s = deepcopy(array_schema)
        s.pop("items")
        with self.assertRaisesRegexp(ValidationError, "Missing properties"):
            Schema.normalize(s)
        # Forgot properties
        s = deepcopy(object_schema)
        s.pop("properties")
        with self.assertRaisesRegexp(ValidationError, "Missing properties"):
            Schema.normalize(s)

    def test_schema_extra_parts(self):
        # object with items
        s = deepcopy(array_schema)
        s["properties"] = object_schema["properties"]
        with self.assertRaisesRegexp(ValidationError, "Unexpected properties"):
            Schema.normalize(s)
        # array with properties
        s = deepcopy(object_schema)
        s["items"] = array_schema["items"]
        with self.assertRaisesRegexp(ValidationError, "Unexpected properties"):
            Schema.normalize(s)

    def test_schema_duplicate_properties(self):
        s = deepcopy(object_schema)
        s["properties"][1]["name"] = "foo"
        with self.assertRaisesRegexp(ValidationError, "Duplicate properties"):
            Schema.normalize(s)

    def test_schema_not_object(self):
        with self.assertRaisesRegexp(ValidationError, "Invalid schema: True"):
            Schema.normalize(True)

    def test_schema_unknown_type(self):
        with self.assertRaisesRegexp(ValidationError, "Unknown type"):
            Schema.normalize({"type": "number"})

    def test_deep_schema_validation_stack(self):
        with self.assertRaisesRegexp(ValidationError, "[0]"):
            deep_normalizer.normalize_data([{"foo": True, "bar": False}])


class TestFloatModel(TestCase):

    def test_normalize(self):
        self.assertEqual(FloatModel.normalize(1), 1.0)
        self.assertEqual(FloatModel.normalize(1.0), 1.0)
        with self.assertRaisesRegexp(ValidationError, "Invalid float"):
            FloatModel.normalize(True)

    def test_serialize(self):
        self.assertEqual(FloatModel.serialize(1.1), 1.1)


class TestIntegerModel(TestCase):

    def test_normalize(self):
        self.assertEqual(IntegerModel.normalize(1), 1)
        self.assertEqual(IntegerModel.normalize(1.0), 1)
        with self.assertRaisesRegexp(ValidationError, "Invalid integer"):
            IntegerModel.normalize(1.1)

    def test_serialize(self):
        self.assertEqual(IntegerModel.serialize(1), 1)


class TestBooleanModel(TestCase):

    def test_normalize(self):
        self.assertEqual(BooleanModel.normalize(True), True)
        with self.assertRaisesRegexp(ValidationError, "Invalid boolean"):
            BooleanModel.normalize(0)

    def test_serialize(self):
        self.assertEqual(BooleanModel.serialize(True), True)


class TestStringModel(TestCase):

    def test_string(self):
        self.assertEqual(StringModel.normalize("omg"), u"omg")
        self.assertEqual(StringModel.normalize(u"omg"), u"omg")
        with self.assertRaisesRegexp(ValidationError, "Invalid string"):
            StringModel.normalize(0)
        with self.assertRaisesRegexp(UnicodeDecodeValidationError, "invalid start byte"):
            StringModel.normalize("\xff")

    def test_serialize(self):
        self.assertEqual(StringModel.serialize("yo"), "yo")


class TestBinaryModel(TestCase):

    def test_binary(self):
        self.assertEqual(BinaryModel.normalize('YWJj'), "abc")
        self.assertEqual(BinaryModel.normalize(u'YWJj'), "abc")
        with self.assertRaisesRegexp(ValidationError, "Invalid base64"):
            # Will complain about incorrect padding
            BinaryModel.normalize("a")
        with self.assertRaisesRegexp(ValidationError, "Invalid binary"):
            BinaryModel.normalize(1)

    def test_serialize(self):
        self.assertEqual(BinaryModel.serialize("abc"), "YWJj")


class TestArrayModel(TestCase):

    def test_normalize(self):
        self.assertEqual(array_normalizer.normalize_data([True, False]), [True, False])
        with self.assertRaisesRegexp(ValidationError, "Invalid array"):
            array_normalizer.normalize_data(("no", "tuples",))
        with self.assertRaisesRegexp(ValidationError, "Invalid boolean"):
            array_normalizer.normalize_data([True, False, 1])


class TestObjectModel(TestCase):

    def test_normalize(self):
        res = object_normalizer.normalize_data({"foo": True, "bar": 2.0})
        self.assertEqual(res, {"foo": True, "bar": 2})
        with self.assertRaisesRegexp(ValidationError, "Invalid object"):
            object_normalizer.normalize_data([])
        # Problems with properties
        with self.assertRaisesRegexp(ValidationError, "Missing properties"):
            object_normalizer.normalize_data({"bar": 2.0})
        with self.assertRaisesRegexp(ValidationError, "Unexpected properties"):
            object_normalizer.normalize_data({"foo": True, "barr": 2.0})


class TestClassModel(TestCase):

    def setUp(self):
        class RecipeModel(ClassModel):
            properties = [
                {
                    "name": "author",
                    "required": True,
                    "schema": Schema.normalize({"type": "string"})
                },
                {
                    "name": "spicy",
                    "required": False,
                    "schema": Schema.normalize({"type": "boolean"})
                },
                {
                    "name": "meta",
                    "required": False,
                    "schema": Schema.normalize({"type": "json"})
                }
            ]

        self.RecipeModel = RecipeModel
        self.recipe = RecipeModel.normalize({
            "author": "Alex",
            "spicy": True
        })
        self.special_recipe = RecipeModel.normalize({
            "author": "Kyu",
            "meta": {"secret": True}
        })

    def test_normalize_okay(self):
        self.assertEqual(self.recipe.data, {
            u"author": u"Alex",
            u"spicy": True
        })
        self.assertTrue(isinstance(self.special_recipe.data["meta"], JSONData))

    def test_normalize_fail(self):
        with self.assertRaisesRegexp(ValidationError, "Missing properties"):
            recipe = self.RecipeModel.normalize({
                "maker": "Alex",
                "spicy": True
            })

    def test_getattr(self):
        self.assertEqual(self.recipe.author, "Alex")
        self.assertEqual(self.recipe.spicy, True)
        self.assertEqual(self.recipe.meta, None)
        with self.assertRaises(AttributeError):
            self.recipe.vegetarian

    def test_setattr(self):
        self.recipe.spicy = False
        self.assertEqual(self.recipe.data, {
            u"author": u"Alex",
            u"spicy": False
        })

    def test_setattr_None_then_serialize(self):
        self.recipe.spicy = None
        self.assertEqual(self.recipe.serialize(), {
            u"author": u"Alex"
        })

    def test_serialize_okay(self):
        self.assertEqual(self.special_recipe.serialize(), {
            u"author": u"Kyu",
            u"meta": {u"secret": True}
        })

    def test_get_schema(self):
        self.assertEqual(self.RecipeModel.get_schema().serialize(), {
            "type": "object",
            "properties": [
                {
                    "name": "author",
                    "required": True,
                    "schema": {"type": "string"}
                },
                {
                    "name": "spicy",
                    "required": False,
                    "schema": {"type": "boolean"}
                },
                {
                    "name": "meta",
                    "required": False,
                    "schema": {"type": "json"}
                }
            ]
        })

class TestJSONData(TestCase):

    def test_normalize(self):
        for i in [1, True, 2.3, "blah", [], {}]:
            self.assertEqual(JSONData.normalize(i).data, i)

    def test_from_string(self):
        j = JSONData.from_string('{"a": 1}')
        self.assertTrue(isinstance(j, JSONData))
        self.assertEqual(j.data, {"a": 1})
        j = JSONData.from_string('')
        self.assertEqual(j, None)

    def test_to_string(self):
        j = JSONData.normalize({"a": 1})
        self.assertEqual(JSONData.to_string(j), '{"a": 1}')
        self.assertEqual(JSONData.to_string(None), '')

    def test_repr_simple(self):
        j = JSONData(True)
        self.assertEqual(repr(j), "<JSONData true>")
        j = JSONData({"a":1, "b": [1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5]})
        self.assertEqual(repr(j), '<JSONData {"a": 1, "b": [1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5]}>')

    def test_repr_truncated(self):
        j = JSONData({"a":1, "b": [1, 2, 3, 4, 5, 6, 7, 8, 9, 8, 7, 6, 5], "c": True, "d": False})
        self.assertEqual(repr(j), '<JSONData {"a": 1, "c": true, "b": [1, 2, 3, 4, 5, 6, 7, 8, 9, 8,  ...>')


class TestNormalizeSerializeJSON(TestCase):

    def test_normalize_json(self):
        arr = [True, False, True]
        with self.assertRaisesRegexp(ValidationError, "Expected JSONData"):
            normalize_json(array_normalizer, None)
        with self.assertRaisesRegexp(ValidationError, "Expected None"):
            normalize_json(None, arr)
        self.assertEqual(normalize_json(array_normalizer, JSONData(arr)), arr)
        self.assertEqual(normalize_json(None, None), None)

    def test_serialize_json(self):
        arr = [True, False, True]
        with self.assertRaisesRegexp(ValidationError, "Expected data"):
            serialize_json(array_normalizer, None)
        with self.assertRaisesRegexp(ValidationError, "Expected None"):
            serialize_json(None, arr)
        self.assertEqual(serialize_json(array_normalizer, arr).data, arr)
        self.assertEqual(serialize_json(None, None), None)


class TestCustomType(TestCase):

    def setUp(self):

        class FrenchBoolean(Model):

            @classmethod
            def normalize(cls, datum):
                return {"Oui": True, "Non": False}[datum]

            @classmethod
            def serialize(cls, datum):
                return {True: "Oui", False: "Non"}[datum]

        def fetcher(name):
            if name == "test.FrenchBoolean":
                return FrenchBoolean
            raise ValidationError("Unknown model")

        self.FrenchBoolean = FrenchBoolean
        self.fetcher = fetcher

    def test_resolve(self):
        s = Schema.normalize({"type": "test.FrenchBoolean"})
        self.assertEqual(s.__class__, SimpleSchema)
        self.assertEqual(s.model_cls, None)
        s.resolve(self.fetcher)
        self.assertEqual(s.model_cls, self.FrenchBoolean)
        self.assertEqual(s.normalize_data("Oui"), True)

    def test_resolve_recursive(self):
        s = Schema.normalize({
            "type": "object",
            "properties": [
                {
                    "name": "a",
                    "required": True,
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "test.FrenchBoolean"
                        }
                    }
                }
            ]
        })
        s.resolve(self.fetcher)
        self.assertEqual(s.normalize_data({"a": ["Oui"]}), {"a": [True]})

