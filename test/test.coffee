assert = require 'assert'
t = require '../teleport.coffee'
tests = require './suite.json'

describe 'Teleport auto-test', ->

  for test in tests
    {schema, fail, pass} = test

    s = t.Schema.fromJson schema
    for p in pass
      console.log "P", JSON.stringify(schema), JSON.stringify p
      it 'should pass', ->
        s.fromJson p
    for f in fail
      console.log "F", JSON.stringify(schema), JSON.stringify f
      it 'should fail', ->
      assert.throws ->
        s.fromJson f



