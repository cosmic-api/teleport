_ = require 'underscore'
assert = require 'assert'
t = require '../teleport.coffee'
tests = require './suite.json'


samesies = ["String", "Integer", "Float", "Boolean", "JSON"]

for test in tests
  {schema, fail, pass} = test

  describe "Auto-test #{JSON.stringify schema}", ->
    s = t.Schema.fromJson schema
    _.each pass, (p) ->
      it "should pass #{JSON.stringify p}", ->
        assert.doesNotThrow ->
          s.fromJson p
      if schema.type in samesies
        it "should deserialize #{JSON.stringify p}", ->
          assert.deepEqual p, s.fromJson p
      # ISO 8601 doesn't have a normalized form
      if schema.type != 'DateTime'
        it "should reserialize #{JSON.stringify p}", ->
          assert.deepEqual p, s.toJson s.fromJson p
    _.each fail, (f) ->
      it "should fail #{JSON.stringify f}", ->
        assert.throws ->
          s.fromJson f

describe "Test native form", ->
  it 'Should deserialize Array', ->
    schema = t.Array(t.Binary)
    assert.deepEqual ['abc', 'xyz'], schema.fromJson ['YWJj', 'eHl6']
  it 'Should deserialize Struct', ->
    schema = t.Struct({
      map:
        a:
          required: true
          schema: t.Binary
      order: ['a']
    })
    assert.deepEqual {a: 'abc'}, schema.fromJson {a: 'YWJj'}
  it 'Should deserialize Map', ->
    schema = t.Map(t.Binary)
    assert.deepEqual {a: 'abc', b: 'xyz'}, schema.fromJson {a: 'YWJj', b: 'eHl6'}
  it 'Should deserialize OrderedMap', ->
    schema = t.OrderedMap(t.Binary)
    assert.deepEqual {
      map:
        a: 'abc'
        b: 'xyz'
      order: ['a', 'b']
    }, schema.fromJson {
      map:
        a: 'YWJj'
        b: 'eHl6'
      order: ['a', 'b']
    }

describe "Test extending Teleport", ->
  YesNoMaybe = {
    typeName: 'YesNoMaybe'
    fromJson: (datum) ->
      if datum in [true, false, null]
        return datum
      throw Error("Invalid YesNoMaybe #{JSON.stringify datum}")
    toJson: (datum) -> datum
  }
  t2 = t.makeTypes (name) ->
    if name == "YesNoMaybe"
      return YesNoMaybe
  it 'Should work', ->
    assert.equal YesNoMaybe, t2.Schema.fromJson {type: "YesNoMaybe"}
    schema = t2.Schema.fromJson {
      type: "Array",
      param:
        type: "YesNoMaybe"
    }
    assert.deepEqual [true, false, null], schema.fromJson [true, false, null]
    assert.throws ->
      schema.fromJson [true, false, ""]



