from unittest2 import TestCase
from teleport.examples import t


class CustomTypeTest(TestCase):

    def test_Color(self):
        self.assertTrue(t("Color").contains('#ffffff'))
        self.assertFalse(t("Color").contains('yellow'))
        self.assertTrue(t({"Array": "Color"}).contains(['#ffffff', '#000000']))

    def test_Nullable(self):
        self.assertTrue(t({"Nullable": "Integer"}).contains(1))
        self.assertTrue(t({"Nullable": "Integer"}).contains(None))
        self.assertFalse(t({"Nullable": "Integer"}).contains(True))
