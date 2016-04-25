package teleport;

import haxe.ds.Either;
import haxe.ds.Option;
import haxe.ds.StringMap;
using Lambda;

import teleport.Util;
import teleport.JsonTools;
import teleport.SchemaTools;


typedef NativeJson = Dynamic;


enum Err {
    ErrValue(message:String, value:JsonValue);
    ErrPosArray(position:Int, err:Err);
    ErrPosObject(position:String, err:Err);
}



class Teleport {

    public function new() {}

    public function validate(schema:Schema, datum:JsonValue):Bool {
        // Use validation logic embedded in the serializer
        return switch this.deserialize(schema, datum) {
            case Right(_): true;
            case Left(_): false;
        }
    }

    public function wrapNativeJson(value:NativeJson) {
        return JsonTools.wrap(value);
    }

    public function deserializeNativeJson(schema:Schema, value:NativeJson) {
        return this.deserialize(schema, this.wrapNativeJson(value));
    }

    public function deserialize(schema:Schema, datum:JsonValue):Either<Err, Dynamic> {
        return switch schema {
            case TAny: Right(datum);
            case TString: switch datum {
                case JString(_): Right(datum);
                default: Left(ErrValue("Invalid string", datum));
            };
            case TDateTime: switch datum {
                case JString(s): switch Util.parseRfc3999(s) {
                    case None: Left(ErrValue("Invalid datetime", datum));
                    case Some(d): Right(d);
                };
                default: Left(ErrValue("Invalid datetime", datum));
            };
            case TInteger: switch datum {
                case JNumber(n): if (Std.is(n, Int)) {
                    Right(n);
                } else {
                    Left(ErrValue("Not an integer", datum));
                };
                default: Left(ErrValue("Not an integer", datum));
            };
            case TFloat: switch datum {
                case JNumber(n): Right(n);
                default: Left(ErrValue("Invalid float", datum));
            };
            case TBoolean: switch datum {
                case JBoolean(b): Right(b);
                default: Left(ErrValue("Invalid boolean", datum));
            };
            case TSchema: switch SchemaTools.schemaFromJsonValue(datum) {
                case Right(schema): Right(schema);
                case Left(_): Left(ErrValue("Invalid schema", datum));
            };
            case TArray(itemSchema): switch datum {
                case JArray(items): {
                    var arr = [];
                    for (i in 0...items.length) {
                        switch this.deserialize(itemSchema, items[i]) {
                            case Right(item): {
                                arr.push(item);
                            };
                            case Left(err): {
                                return Left(ErrPosArray(i, err));
                            }
                        }
                    }
                    return Right(arr);
                };
                default: Left(ErrValue("Not an array", datum));
            };
            case TMap(itemSchema): switch datum {
                case JObject(items): {
                    var m = new StringMap();
                    for (k in items.keys()) {
                        var v = items.get(k);
                        switch this.deserialize(itemSchema, v) {
                            case Right(item): {
                                m.set(k, item);
                            };
                            case Left(err): {
                                return Left(ErrPosObject(k, err));
                            }
                        }
                    }
                    return Right(m);
                };
                default: Left(ErrValue("Not an object", datum));
            };
            case TObject(itemSchemas): switch datum {
                case JObject(items): {
                    var m = new StringMap();
                    for (k in itemSchemas.keys()) {
                        var required = itemSchemas.get(k).required;
                        var s = itemSchemas.get(k).schema;
                        if (items.exists(k)) {
                            var v = items.get(k);
                            switch this.deserialize(s, v) {
                                case Right(item): {
                                    m.set(k, item);
                                };
                                case Left(err): {
                                    return Left(ErrPosObject(k, err));
                                }
                            }
                        } else if (required) {
                            return Left(ErrValue("Missing required attribute", datum));
                        }
                    }
                    return Right(m);
                };
                default: Left(ErrValue("Not an object", datum));
            }
        }
    }
}
