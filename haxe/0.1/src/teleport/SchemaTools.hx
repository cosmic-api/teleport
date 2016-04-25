package teleport;

import haxe.ds.Either;
import haxe.ds.StringMap;

import teleport.JsonTools;


typedef SchemaError = String;


enum Schema {
    TAny;
    TString;
    TBoolean;
    TInteger;
    TDateTime;
    TFloat;
    TSchema;
    TArray(items:Schema);
    TMap(items:Schema);
    TObject(items:StringMap<{schema:Schema, required:Bool}>);
}


class SchemaTools {

    public static function schemaFromJsonValue(datum:JsonValue):Either<SchemaError, Schema> {
        return switch datum {
            case JString(s): switch s {
                case "String": Right(TString);
                case "Boolean": Right(TBoolean);
                case "Integer": Right(TInteger);
                case "DateTime": Right(TDateTime);
                case "Float": Right(TFloat);
                case "Schema": Right(TSchema);
                default: Left("Unknown type $s");
            };
            case JObject(items): {
                if (items.exists("Array")) {
                    switch SchemaTools.schemaFromJsonValue(items.get("Array")) {
                        case Right(paramSchema): Right(TArray(paramSchema));
                        case Left(err): Left(err);
                    };
                } else if (items.exists("Map")) {
                    switch SchemaTools.schemaFromJsonValue(items.get("Map")) {
                        case Right(paramSchema): Right(TMap(paramSchema));
                        case Left(err): Left(err);
                    };
                } else if (items.exists("Struct")) {
                    SchemaTools.structSchemaFromParam(items.get("Struct"));
                } else {
                    Left("Unknown schema");
                };
            }
            default: Left("Unknown type");
        }
    }

    static function structSchemaFromParam(param:JsonValue):Either<SchemaError, Schema> {
        switch param {
            case JObject(items): {
                var m = new StringMap();
                var required = items.get("required");
                var optional = items.get("optional");

                if (required != null) {
                    switch (required) {
                        case JObject(req): {
                            for (k in req.keys()) {
                                switch SchemaTools.schemaFromJsonValue(req.get(k)) {
                                    case Right(s): m.set(k, {required: true, schema: s});
                                    case Left(err): return Left(err);
                                }
                            }
                        };
                        default: return Left("required not an object");
                    }
                }

                if (optional != null) {
                    switch (optional) {
                        case JObject(opt): {
                            for (k in opt.keys()) {
                                switch SchemaTools.schemaFromJsonValue(opt.get(k)) {
                                    case Right(s): m.set(k, {required: false, schema: s});
                                    case Left(err): return Left(err);
                                }
                            }
                        };
                        default: return Left("optional not an object");
                    }

                }

                return Right(TObject(m));

            };
            default: return Left("Invalid");
        };
    }
}
