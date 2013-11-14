import json
from unittest2 import TestCase, TestSuite, defaultTestLoader

from teleport import *


tests_schema = Array(Struct([
    required("schema", Schema()),
    required("pass", Array(JSON())),
    required("fail", Array(JSON())),
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
        t(  
            schema=Integer(),
            all=primitives,
            passing=[Box(-1), Box(1), Box(1.0)]),
        t(
            schema=Boolean(),
            all=primitives,
            passing=[Box(True), Box(False)]),
        t(
            schema=String(),
            all=primitives,
            passing=[Box("")]),
        t(
            schema=Float(),
            all=primitives,
            passing=[Box(-1), Box(1), Box(1.0), Box(1.1)]),
        t(
            schema=DateTime(),
            failing=primitives + [Box("2013-10-04 13:05:25.354952")], # Needs a T
            passing=[Box("2013-10-04T13:05:25.354952")]),
        t(
            schema=Array(Integer()),
            passing=[Box([]), Box([1]), Box([1.0])],
            failing=set(primitives + [Box([1.1])]) - set([Box([])])),
        t(
            schema=Map(Integer()),
            passing=[Box({}), Box({"a": 1}), Box({"a": 1.0})],
            failing=set(primitives) - set([Box({})])),
        t(
            schema=Struct([
                required("a", Integer()),
                optional("b", Integer())
            ]),
            passing=[Box({"a": 1, "b": 2}), Box({"a": 1}), Box({"a": 1.0})],
            failing=set(primitives) | set([Box({"a": 1.1}), Box({"b": 1})])),
        t(
            schema=Struct([]),
            passing=[Box({})],
            failing=set(primitives) - set([Box({})])),
        t(
            schema=Tuple([Integer(), String()]),
            passing=[Box([1, ""]), Box([1.0, "2"])],
            failing=set(primitives) | set([Box([1]), Box([1.1, ""]), Box([1, "1", "2"])])),
        t(
            schema=Binary(),
            passing=[Box('YWJj')],
            failing=set(primitives + [Box('a')]) - set([Box("")])),
        t(
            schema=JSON(),
            passing=primitives,
            failing=[]),
        t(
            schema=Schema(),
            passing=map(Box, Array(Schema()).to_json([
                String(), Boolean(), Integer(), Float(), Binary(),
                DateTime(), JSON(), Schema(),
                Array(Integer()),
                Struct([required('a', Integer())]),
                Map(Integer()),
                OrderedMap(Integer()),
            ])),
            failing=primitives + [
                Box({"type": "string"}), # case-sensitive
                Box({"type": "XXX"}), # unknown type
                Box({"type": "String", "param": True}), # unexpected param
                Box({"type": "Array"}), # missing param
            ]),
        t(
            schema=OrderedMap(Integer()),
            passing=[
                Box({"map": {}, "order": []}),
                Box({"map": {"a": 1, "b": 2}, "order": ["a", "b"]}),
            ],
            failing=primitives + [
                Box({"map": {"a": 1, "b": 2}, "order": ["a"]}),
                Box({"map": {"a": 1, "b": 2}, "order": ["a", "b", "b"]}),
                Box({"map": {"a": 1, "b": 2}}),
                Box({"order": ["a", "b", "b"]}),
                Box({"map": {"a": 1, "b": 2}, "what": 3, "order": ["a", "b", "b"]}),
            ]),
    ]
    return tests

def make_pass(schema, datum):
    class T(TestCase):
        def test_passing(self):
            schema.from_json(datum)
    return T('test_passing')

def make_reserialize(schema, datum):
    class T(TestCase):
        def test_reserialize(self):
            self.assertEqual(
                schema.to_json(schema.from_json(datum)),
                datum)
    return T('test_reserialize')

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
            datum = json.loads(json.dumps(p.datum))
            suite.addTest(make_pass(test['schema'], datum))
            suite.addTest(make_reserialize(test['schema'], datum))
        for f in test['fail']:
            datum = json.loads(json.dumps(f.datum))
            suite.addTest(make_fail(test['schema'], datum))
    return suite

if __name__ == "__main__":
    tests = make_json_suite()
    print json.dumps(tests_schema.to_json(tests), sort_keys=True)
