import sys
import os
import unittest2

from draft02_suite import suite as tests

sys.path.append(os.path.join('../python', os.path.dirname(__file__)))
from teleport import t


def make_pass_test(schema, datum):
    class T(unittest2.TestCase):
        def test_passing(self):
            if not t(schema).check(datum):
                raise Exception()
    return T('test_passing')


def make_fail_test(schema, datum):
    class T(unittest2.TestCase):
        def test_failing(self):
            if t(schema).check(datum):
                raise Exception()
    return T('test_failing')


def load_tests(_1, _2, _3):

    suite = unittest2.TestSuite()
    for test in tests:
        for datum in test['passing']:
            suite.addTest(make_pass_test(test['schema'], datum))
        for datum in test['failing']:
            suite.addTest(make_fail_test(test['schema'], datum))

    return suite


if __name__ == "__main__":
    unittest2.main()
