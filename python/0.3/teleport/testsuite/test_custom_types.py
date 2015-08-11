import unittest2

from teleport.examples import t
from teleport.compat import PY3, PYPY


class CustomTypeTest(unittest2.TestCase):

    def test_Color(self):
        self.assertTrue(t("Color").contains('#ffffff'))
        self.assertFalse(t("Color").contains('yellow'))
        self.assertTrue(t({"Array": "Color"}).contains(['#ffffff', '#000000']))

    def test_Nullable(self):
        self.assertTrue(t({"Nullable": "Integer"}).contains(1))
        self.assertTrue(t({"Nullable": "Integer"}).contains(None))
        self.assertFalse(t({"Nullable": "Integer"}).contains(True))
        self.assertEqual(t({"Nullable": "Integer"}).from_json(1), 1)
        self.assertEqual(t({"Nullable": "Integer"}).from_json(None), None)

        s = t({"Array": {"Nullable": "String"}})

        self.assertTrue(s.contains(["sparse", None, "arrays", None, None, None, "what"]))

        s = t({"Struct": {
                 "required": {"id": "Integer"},
                 "optional": {"name": {"Nullable": "String"},
                              "age":  {"Nullable": "Integer"}}}})

        self.assertTrue(s.contains({"id": 1, "name": "Jake", "age": 28}))
        self.assertTrue(s.contains({"id": 1, "name": None, "age": 12}))
        self.assertTrue(s.contains({"id": 1, "age": None}))

    @unittest2.skipIf(PYPY or PY3, "Skipping pickle test for PyPy and Python3")
    def test_PythonObject(self):
        self.assertEqual(t("PythonObject").to_json(1), 'I1\n.')
        self.assertEqual(t("PythonObject").to_json({1, 2}),
            'c__builtin__\nset\np0\n((lp1\nI1\naI2\natp2\nRp3\n.')
        self.assertEqual(t("PythonObject").from_json(
            'c__builtin__\nset\np0\n((lp1\nI1\naI2\natp2\nRp3\n.'), {1, 2})
