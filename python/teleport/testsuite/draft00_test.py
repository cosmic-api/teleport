import json
from unittest2 import TestCase, TestSuite, defaultTestLoader

from teleport.legacy import *
from teleport.draft00 import t as t


def make_pass_test(schema, datum):
    class T(TestCase):
        def test_passing(self):
            if datum not in schema:
                raise Exception()
    return T('test_passing')


def make_fail_test(schema, datum):
    class T(TestCase):
        def test_failing(self):
            if datum in schema:
                raise Exception()
    return T('test_failing')


primitives = {
    Box(-1),
    Box(1),
    Box(1.0),
    Box(1.1),
    Box(True),
    Box(False),
    Box(u""),
    Box(u"2007-04-05T14:30"),
    Box(u"Boolean"),
    Box({}),
    Box([]),
    Box(None)
}


ttt = [
    {
        "schema": t("Integer"),
        "all": primitives,
        "pass": {Box(-1), Box(1), Box(3123342342349238429834)}
    },
    {
        "schema": t("Float"),
        "all": primitives,
        "pass": {Box(1e4), Box(1.0), Box(1.1)}
    },
    {
        "schema": t("Boolean"),
        "all": primitives,
        "pass": {Box(True), Box(False)}
    },
    {
        "schema": t("String"),
        "all": primitives,
        "pass": {Box(u""), Box(u"2007-04-05T14:30"), Box(u"Boolean")}
    },
    {
        "schema": t("JSON"),
        "all": primitives,
        "fail": set()
    },
    {
        "schema": t("DateTime"),
        "all": primitives,
        "pass": {Box(u"2007-04-05T14:30")}
    },
    {
        "schema": t("Schema"),
        "all": primitives,
        "pass": {
            Box(u"Integer"),
            Box(u"Float"),
            Box(u"Boolean"),
            Box(u"String"),
            Box(u"JSON"),
            Box(u"DateTime"),
            Box(u"Schema")
        }
    }
]


for tt in ttt:
    if "all" in tt:
        if "fail" in tt:
            tt["pass"] = tt["all"] - tt["fail"]
        elif "pass" in tt:
            tt["fail"] = tt["all"] - tt["pass"]


def suite():
    suite = TestSuite()
    for test in ttt:
        for p in test['pass']:
            datum = json.loads(json.dumps(p.datum))
            suite.addTest(make_pass_test(test['schema'], datum))
        for f in test['fail']:
            datum = json.loads(json.dumps(f.datum))
            suite.addTest(make_fail_test(test['schema'], datum))
    return suite

