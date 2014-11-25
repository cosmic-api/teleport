from unittest2 import TestCase
from teleport.examples import t


class ExtendingTest(TestCase):

    def test_extend(self):
        self.assertTrue(t("Color").contains('#ffffff'))
        self.assertFalse(t("Color").contains('yellow'))
        self.assertTrue(t({"Array": "Color"}).contains(['#ffffff', '#000000']))

