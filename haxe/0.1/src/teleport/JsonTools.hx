package teleport;
import haxe.Json;
import haxe.ds.Option;
import haxe.ds.StringMap;

using Lambda;

enum JsonValue {
    JNull;
    JBoolean(b:Bool);
    JNumber(i:Float);
    JString(s:String);
    JArray(items:Array<JsonValue>);
    JObject(items:StringMap<JsonValue>);
}

enum JsonType {
    JTNull;
    JTBoolean;
    JTNumber;
    JTString;
    JTArray;
    JTObject;
}

class JsonWrapper {

    public function guessType(object:Dynamic):Option<JsonType> {
        return if (Std.is(object, Float)) { // Remember that a Haxe Int is also a Float
            Some(JTNumber);
        } else if (Std.is(object, Bool)) {
            Some(JTBoolean);
        } else if (Std.is(object, String)) {
            Some(JTString);
        } else if (object == null) {
            Some(JTNull);
        } else if (Std.is(object, Array)) {
            Some(JTArray);
        } else if (Std.is(object, StringMap)) {
            Some(JTObject);
        } else {
            None;
        }
    }

//    public function wrap(object:Dynamic):Option<J> {
//
//
//    }

}


class JsonTools {

    public static function wrap(datum:Dynamic):JsonValue {
        if (Std.is(datum, Float)) { // Remember that an Int is also a Float
            return JNumber(datum);
        } else if (Std.is(datum, Bool)) {
            return JBoolean(datum);
        } else if (Std.is(datum, String)) {
            return JString(datum);
        } else if (datum == null) {
            return JNull;
        } else if (Std.is(datum, Array)) {
            return JArray(Lambda.array(Lambda.map(datum, JsonTools.wrap)));
        } else if (Std.is(datum, StringMap)) {
            return JObject(datum);
        } else {
            var s = new StringMap();
            for (f in Reflect.fields(datum)) {
                s.set(f, JsonTools.wrap(Reflect.field(datum, f)));
            }
            return JObject(s);
        }
    }

    public static function unwrap(datum:JsonValue):Dynamic {
        return switch datum {
            case JNull: null;
            case JBoolean(o): o;
            case JNumber(o): o;
            case JString(o): o;
            case JArray(items): [for (i in items) JsonTools.unwrap(i)];
            case JObject(items): {
                var ret = new StringMap();
                for (k in items.keys()) {
                    ret.set(k, JsonTools.unwrap(items.get(k)));
                }
                ret;
            };
        }
    }

    public static function parse(s:String):Option<JsonValue> {
        var parsed;
        try {
            parsed = Json.parse(s);
        } catch (e:Dynamic) {
            return Option.None;
        }
        return Option.Some(JsonTools.wrap(parsed));
    }

    public static function parseUnsafe(s:String):JsonValue {
        switch JsonTools.parse(s) {
            case Option.Some(j): return j;
            case Option.None: throw "Invalid JSON";
        }
    }

    public static function stringify(datum:JsonValue):String {
        return Json.stringify(JsonTools.unwrap(datum));
    }
}
