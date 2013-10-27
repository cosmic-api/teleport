_ = require 'underscore'
assert = require 'assert'
t = require '../teleport.coffee'
tests = require './suite.json'

for test in tests
  {schema, fail, pass} = test

  describe "#{JSON.stringify schema}", ->
    s = t.Schema.fromJson schema
    _.each pass, (p) ->
      it "should pass #{JSON.stringify p}", ->
        assert.doesNotThrow ->
          s.fromJson p
    _.each fail, (f) ->
      it "should fail #{JSON.stringify f}", ->
        assert.throws ->
          s.fromJson f



