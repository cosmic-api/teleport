assert = require 'assert'
t = require '../teleport.coffee'
tests = require './suite.json'

skip = ["Struct", "OrderedMap", "Binary", "JSON", "Schema"]

describe 'Teleport auto-test', ->

  for test in tests
    {schema, fail, pass} = test

    if schema.type in skip
      continue

    s = t.Schema.fromJson schema
    _s = JSON.stringify schema
    for p in pass
      _p = JSON.stringify p
      it "should pass #{_s} #{_p}", ->
        s.fromJson p
    for f in fail
      _f = JSON.stringify f
      it "should fail #{_s} #{_f}", ->
        assert.throws ->
          s.fromJson f



