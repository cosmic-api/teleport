_ = require 'underscore'


BasicPrimitive =
  toJson: (datum) ->
    return datum


Schema = _.extend {}, BasicPrimitive, {
  fromJson: (datum) ->
    if datum.type == "Float"
      return Float
    else if datum.type == "Integer"
      return Integer
    else if datum.type == "Schema"
      return Schema
}


Integer = _.extend {}, BasicPrimitive, {
  fromJson: (datum) ->
    """If *datum* is an integer, return it; if it is a float with a 0 for
    its fractional part, return the integer part as an int. Otherwise,
    raise a :exc:`ValidationError`.
    """
    if _.isNumber(datum) and datum % 1 == 0
      return datum
    throw new Error()
}


Float  = _.extend {}, BasicPrimitive, {
  fromJson: (datum) ->
    """If *datum* is an integer, return it; if it is a float with a 0 for
    its fractional part, return the integer part as an int. Otherwise,
    raise a :exc:`ValidationError`.
    """
    if _.isNumber(datum)
      return datum
    throw new Error()
}


root =
  Schema: Schema
  Integer: Integer
  Float: Float


# If no framework is available, just export to the global object (window.HUSL
# in the browser)
@teleport = root unless module? or jQuery? or requirejs?
# Export to Node.js
module.exports = root if module?
# Export to RequireJS
define(root) if requirejs? and define?