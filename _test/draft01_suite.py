import json
from unittest2 import TestCase, TestSuite


class Box(object):
    """Used as a wrapper around JSON data to disambiguate None as a JSON value
    (``null``) from None as an absence of value. Its :attr:`datum` attribute
    will hold the actual JSON value.

    For example, an HTTP request body may be empty in which case your function
    may return ``None`` or it may be "null", in which case the function can
    return a :class:`Box` instance with ``None`` inside.
    """
    def __init__(self, datum):
        self.datum = datum

    def __hash__(self):
        return hash(json.dumps(self.datum))

    def __eq__(self, datum):
        return self.datum == datum


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
        "schema": "Integer",
        "all": primitives,
        "pass": {Box(-1), Box(1), Box(3123342342349238429834)}
    },
    {
        "schema": "Float",
        "all": primitives,
        "pass": {Box(1e4), Box(1.0), Box(1.1)}
    },
    {
        "schema": "Boolean",
        "all": primitives,
        "pass": {Box(True), Box(False)}
    },
    {
        "schema": "String",
        "all": primitives,
        "pass": {Box(u""), Box(u"2007-04-05T14:30"), Box(u"Boolean")}
    },
    {
        "schema": "JSON",
        "all": primitives,
        "fail": set()
    },
    {
        "schema": "DateTime",
        "all": primitives,
        "pass": {Box(u"2007-04-05T14:30")}
    },
    {
        "schema": {"Array": "Integer"},
        "fail": (primitives - {Box([])}) | {Box([1, True])},
        "pass": {Box([]), Box([1]), Box([2, 3])}
    },
    {
        "schema": {"Map": "Integer"},
        "fail": (primitives - {Box({})}) | {Box({"a": True})},
        "pass": {Box({"a": 1}), Box({"a": -123, "b": 123})}
    },
    {
        "schema": {"Struct": {
            "required": {"a": "Integer"},
            "optional": {"b": "Integer"}}},
        "fail": primitives | {Box({"a": 1.0})},
        "pass": {Box({"a": 1}), Box({"a": -1, "b": 13})}
    },
    {
        "schema": "Schema",
        "all": primitives,
        "pass": {
            Box(u"Integer"),
            Box(u"Float"),
            Box(u"Boolean"),
            Box(u"String"),
            Box(u"JSON"),
            Box(u"DateTime"),
            Box(u"Schema"),
            Box({"Array": "String"}),
            Box({"Map": "String"}),
            Box({"Struct": { # Test metadata support added in draft-01
                "required": {},
                "optional": {},
                "doc.order": []
            }})
        }
    }
]


for tt in ttt:
    if "all" in tt:
        if "fail" in tt:
            tt["pass"] = tt["all"] - tt["fail"]
        elif "pass" in tt:
            tt["fail"] = tt["all"] - tt["pass"]

suite = []
for test in ttt:
    suite.append({
        'schema': test['schema'],
        'passing': [p.datum for p in test['pass']],
        'failing': [p.datum for p in test['fail']]
    })


if __name__ == "__main__":
    print json.dumps(suite)
