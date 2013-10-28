_ = require 'underscore'
isostring = require 'isostring'

isObjectNotArray = (datum) ->
  _.isObject(datum) and not _.isArray(datum)

wrap = (assembler) ->
  schema = assembler.wraps

  assembler = _.extend {
      assemble: (datum) -> datum
      disassemble: (datum) -> datum
  }, assembler

  _.extend {}, assembler, {
    toJson: (datum) ->
      schema.toJson assembler.disassemble datum
    fromJson: (datum) ->
      assembler.assemble schema.fromJson datum
  }

makeTypes = (getter) ->

  Schema = {
    typeName: 'Schema'
    toJson: (datum) ->
      ret = type: datum.typeName
      if datum.paramSchema != undefined
        ret.param = datum.paramSchema.toJson datum.param
      return ret
    fromJson: (datum) ->
      schema = root[datum.type]
      if schema == undefined
        schema = getter(datum.type)
      if schema != undefined
        if schema.paramSchema != undefined
          param = schema.paramSchema.fromJson datum.param
          return schema(param)
        else if datum.param != undefined
          throw new Error("Unexpected param")
        else
          return schema
      throw new Error("Unknown type: #{datum.type}")
  }


  Integer = {
    typeName: 'Integer'
    toJson: (datum) -> datum
    fromJson: (datum) ->
      if _.isNumber(datum) and datum % 1 == 0
        return datum
      throw new Error("Invalid Integer: #{datum}")
  }


  Float = {
    typeName: 'Float'
    toJson: (datum) -> datum
    fromJson: (datum) ->
      if _.isNumber(datum)
        return datum
      throw new Error("Invalid Float")
  }


  Boolean = {
    typeName: 'Boolean'
    toJson: (datum) -> datum
    fromJson: (datum) ->
      if _.isBoolean(datum)
        return datum
      throw new Error("Invalid Boolean")
  }


  String = {
    typeName: 'String'
    toJson: (datum) -> datum
    fromJson: (datum) ->
      if _.isString(datum)
        return datum
      throw new Error("Invalid String")
  }


  DateTime = wrap {
    typeName: 'DateTime'
    wraps: String
    assemble: (datum) ->
      if isostring datum
        return new Date Date.parse datum
      throw new Error("Invalid DateTime")
    disassemble: (datum) ->
      return new Buffer(datum).toString 'base64'
  }


  Binary = wrap {
    typeName: 'Binary'
    wraps: String
    assemble: (datum) ->
      s = new Buffer(datum, 'base64').toString 'utf-8'
      if s != ''
        return s
      throw new Error("Invalid base64")
    disassemble: (datum) ->
      return new Buffer(datum).toString 'base64'
  }


  JSON = {
    typeName: 'JSON'
    toJson: (datum) -> datum
    fromJson: (datum) -> datum
  }


  Array = (param) ->
    return {
      typeName: 'Array'
      param: param
      paramSchema: Array.paramSchema
      fromJson: (datum) ->
        if _.isArray(datum)
          return (param.fromJson(item) for item in datum)
        throw new Error()
      toJson: (datum) ->
        return (param.toJson(item) for item in datum)
    }
  Array.paramSchema = Schema


  Map = (param) ->
    return {
      typeName: 'Map'
      param: param
      paramSchema: Map.paramSchema
      fromJson: (datum) ->
        if isObjectNotArray datum
          ret = {}
          for key, value of datum
            ret[key] = param.fromJson value
          return ret
        throw new Error()
      toJson: (datum) ->
        ret = {}
        for key, value of datum
          if value != undefined
            ret[key] = param.toJson value
        return ret
    }
  Map.paramSchema = Schema


  Struct = (param) ->
    return {
      typeName: 'Struct'
      param: param
      paramSchema: Struct.paramSchema
      toJson: (datum) ->
        ret = {}
        for key, value of datum
          if value != undefined
            ret[key] = param.map[key].schema.toJson value
        return ret
      fromJson: (datum) ->
        if isObjectNotArray datum
          ret = {}
          for key, value of datum
            if key not in param.order
              throw new Error "Unexpected key: #{key}"
          for key, spec of param.map
            if datum[key] != undefined
              ret[key] = spec.schema.fromJson datum[key]
            else if spec.required
              throw new Error "Required key missing: #{key}"
          return ret
        throw new Error()
    }


  OrderedMap = (param) ->
    return wrap {
      typeName: 'OrderedMap'
      param: param
      paramSchema: OrderedMap.paramSchema
      wraps: Struct {
        map:
          map:
            required: true
            schema: Map(param)
          order:
            required: true
            schema: Array(String)
        order: ['map', 'order']
      }
      assemble: (datum) ->
        k = _.keys datum.map
        o = datum.order
        if k.length == o.length == _.union(k, o).length
          return datum
        throw new Error("Invalid OrderedMap #{k}, #{o}", k, o)
    }
  OrderedMap.paramSchema = Schema


  Struct.paramSchema = OrderedMap(Struct(
    map:
      required:
        required: true
        schema: Boolean
      schema:
        required: true
        schema: Schema
      doc:
        required: false
        schema: String
    order:
      ['required', 'schema', 'doc']
  ))


  root =
    Schema: Schema
    Integer: Integer
    Float: Float
    Boolean: Boolean
    DateTime: DateTime
    String: String
    Array: Array
    Map: Map
    JSON: JSON
    Binary: Binary
    Struct: Struct
    OrderedMap: OrderedMap

  return root


root = makeTypes(-> undefined)
root.makeTypes = makeTypes

# If no framework is available, just export to the global object (window.HUSL
# in the browser)
@teleport = root unless module? or jQuery? or requirejs?
# Export to Node.js
module.exports = root if module?
# Export to RequireJS
define(root) if requirejs? and define?
