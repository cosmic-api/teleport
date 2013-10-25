_ = require 'underscore'


BasicPrimitive =
  toJson: (datum) ->
    return datum


class ParametrizedPrimitive
  constructor: (@param) ->


Schema = _.extend {}, BasicPrimitive, {
  fromJson: (datum) ->
    schema = root[datum.type]
    if schema != undefined
      if schema.param_schema != undefined
        param = schema.param_schema.fromJson datum.param
        return schema(param)
      else
        return schema
    throw new Error()
}


Integer = _.extend {}, BasicPrimitive, {
  fromJson: (datum) ->
    if _.isNumber(datum) and datum % 1 == 0
      return datum
    throw new Error()
}


Float  = _.extend {}, BasicPrimitive, {
  fromJson: (datum) ->
    if _.isNumber(datum)
      return datum
    throw new Error()
}


Boolean = _.extend {}, BasicPrimitive, {
  fromJson: (datum) ->
    if _.isBoolean(datum)
      return datum
    throw new Error()
}


String = _.extend {}, BasicPrimitive, {
  fromJson: (datum) ->
    if _.isString(datum)
      return datum
    throw new Error()
}


DateTime = _.extend {}, BasicPrimitive, {
  fromJson: (datum) ->
    if _.isString(datum)
      return new Date Date.parse datum
    throw new Error()
  toJson: (datum) ->
    datum.toJSON()
}


Array = (param) ->
  return {
    fromJson: (datum) ->
      if _.isArray(datum)
        return (@param.fromJson(item) for item in datum)
      throw new Error()
    toJson: (datum) ->
      return @param.toJson(item) for item in datum
  }
Array.param_schema = Schema


Map = (param) ->
  return {
    fromJson: (datum) ->
      if _.isObject datum
        ret = {}
        for key, value of datum
          ret[key] = param.fromJson value
        return ret
      throw new Error()
    toJson: (datum) ->
      ret = {}
      for key, value of datum
        ret[key] = param.toJson value
      return ret
  }
Map.param_schema = Schema


Struct = (param) ->
  fromJson: (datum) ->
    if _.isObject datum
      ret = {}
      for key, value of param.map
        ret[key] = value.schema.fromJson datum[key]
      return ret
    throw new Error()
Struct.param_schema = {fromJson: (p) -> p}



root =
  Schema: Schema
  Integer: Integer
  Float: Float
  Boolean: Boolean
  DateTime: DateTime
  String: String
  Array: Array
  Map: Map


# If no framework is available, just export to the global object (window.HUSL
# in the browser)
@teleport = root unless module? or jQuery? or requirejs?
# Export to Node.js
module.exports = root if module?
# Export to RequireJS
define(root) if requirejs? and define?