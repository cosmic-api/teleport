import json
from unittest2 import TestCase, TestSuite, defaultTestLoader

from teleport import *


tests_schema = Array(Struct([
    required("schema", Schema),
    required("pass", Array(JSON)),
    required("fail", Array(JSON)),
]))

primitives = [
    Box(-1),
    Box(1),
    Box(1.0),
    Box(1.1),
    Box(True),
    Box(False),
    Box(""),
    Box({}),
    Box([]),
    Box(None),
]

def t(schema, all=None, passing=None, failing=None):
    if failing is None:
        failing = set(all) - set(passing)
    return {
        "schema": schema,
        "pass": set(passing),
        "fail": failing
    }

def make_json_suite():
    tests = [
        t(Integer, all=primitives, passing=[Box(-1), Box(1), Box(1.0)]),
        t(Boolean, all=primitives, passing=[Box(True), Box(False)]),
        t(String, all=primitives, passing=[Box("")]),
        t(Float, all=primitives, passing=[Box(-1), Box(1), Box(1.0), Box(1.1)]),
        t(DateTime,
            failing=primitives + [Box("2013-10-04 13:05:25.354952")], # Needs a T
            passing=[Box("2013-10-04T13:05:25.354952")])
    ]
    # Binary
    # DateTime
    # Array
    # Struct
    # Map
    # OrderedMap
    return tests

def make_pass(schema, datum):
    class T(TestCase):
        def test_passing(self):
            schema.from_json(datum)
    return T('test_passing')

def make_fail(schema, datum):
    class T(TestCase):
        def test_failing(self):
            with self.assertRaises(ValidationError):
                schema.from_json(datum)
    return T('test_failing')

def suite():
    suite = TestSuite()
    for test in make_json_suite():
        for p in test['pass']:
            suite.addTest(make_pass(test['schema'], p.datum))
        for f in test['fail']:
            suite.addTest(make_fail(test['schema'], f.datum))
    return suite

if __name__ == "__main__":
    tests = make_json_suite()
    print json.dumps(tests_schema.to_json(tests))
