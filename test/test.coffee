assert = require 'assert'
t = require '../teleport.coffee'
tests = require './suite.json'

describe 'Teleport auto-test', ->

  for test in tests
    {schema, fail, pass} = test

    s = t.Schema.fromJson schema
    _s = JSON.stringify schema
    for p in pass
      _p = JSON.stringify p
      it "should pass #{_s} #{_p}", ->
        s.fromJson p
    for f in fail
      _f = JSON.stringify f
      it "should fail #{_s} #{_p}", ->
      assert.throws ->
        s.fromJson f



