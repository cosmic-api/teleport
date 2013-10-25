import json
from copy import deepcopy

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



"""
        self.assertTrue(isinstance(DateTime.from_json('2013-10-04T13:05:25.354952'), datetime))
        self.assertEqual(DateTime.from_json('2013-10-04T13:05:25.354952'), datetime(2013, 10, 4, 13, 5, 25, 354952))
        # Separator must be T!
        with self.assertRaises(ValidationError):
            DateTime.from_json('2013-10-04 13:05:25.354952')
"""

def t(schema, all=None, passing=None, failing=None):
    if failing is None:
        failing = set(all) - set(passing)
    return {
        "schema": schema,
        "pass": set(passing),
        "fail": failing
    }

def make_tests():
    tests = [
        t(Integer, all=primitives, passing=[Box(-1), Box(1), Box(1.0)]),
        t(Boolean, all=primitives, passing=[Box(True), Box(False)]),
        t(String, all=primitives, passing=[Box(""), Box(False)]),
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

if __name__ == "__main__":
    tests = make_tests()
    print json.dumps(tests_schema.to_json(tests))
