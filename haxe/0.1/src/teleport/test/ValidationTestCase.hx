package teleport.test;

import teleport.Teleport;
import teleport.JsonTools;
import teleport.SchemaTools;

import haxe.ds.StringMap;
import haxe.Json;
import haxe.unit.TestCase;


class ValidationTestCase extends TestCase {

    public var structSchemaJson:JsonValue = JsonTools.parseUnsafe('{"Struct": {"required": {"name": "String"}, "optional": {"age": "Integer"}}}');
    public var structSchemaJsonBad:JsonValue = JsonTools.parseUnsafe('{"Struct": {"required": {"name": "String"}, "optional": {"age": "Intege"}}}');

    public var structSchema:Schema = TObject([
        "name" => {required: true, schema: TString},
        "age" => {required: false, schema: TInteger}
    ]);

    public function testValidateInteger() {
        this.assertTrue(new Teleport().validate(TInteger, JNumber(1)));
        this.assertTrue(new Teleport().validate(TInteger, JNumber(1.0)));
        this.assertFalse(new Teleport().validate(TInteger, JNumber(1.1)));
        this.assertFalse(new Teleport().validate(TInteger, JNull));
    }

    public function testValidateString() {
        this.assertTrue(new Teleport().validate(TString, JString("")));
        this.assertTrue(new Teleport().validate(TString, JString("^*#!&(*@&^")));
        this.assertFalse(new Teleport().validate(TString, JNull));
    }

    public function testValidateBoolean() {
        this.assertTrue(new Teleport().validate(TBoolean, JBoolean(true)));
        this.assertTrue(new Teleport().validate(TBoolean, JBoolean(false)));
        this.assertFalse(new Teleport().validate(TBoolean, JNull));
    }

    public function testValidateFloat() {
        this.assertTrue(new Teleport().validate(TFloat, JNumber(1.000)));
        this.assertTrue(new Teleport().validate(TFloat, JNumber(1)));
        this.assertTrue(new Teleport().validate(TFloat, JNumber(1.2132e-243)));
        this.assertFalse(new Teleport().validate(TFloat, JNull));
    }

    public function testValidateSchema() {
        this.assertTrue(new Teleport().validate(TSchema, this.structSchemaJson));
        this.assertFalse(new Teleport().validate(TSchema, this.structSchemaJsonBad));
        this.assertTrue(new Teleport().validate(TSchema, JString("Integer")));
        this.assertFalse(new Teleport().validate(TSchema, JString("Intege")));
        this.assertTrue(new Teleport().validate(TSchema, JsonTools.parseUnsafe('{"Array": "Integer"}')));
    }

    public function testValidateArray() {
        var s = TArray(TInteger);
        var emptyArray = JsonTools.wrap([]);
        var goodArray = JsonTools.wrap([1, 1123]);
        var badArray = JsonTools.wrap([1, 1123.1]);

        this.assertTrue(new Teleport().validate(s, emptyArray));
        this.assertTrue(new Teleport().validate(s, goodArray));
        this.assertFalse(new Teleport().validate(s, badArray));
    }

    public function testValidateMap() {
        var s = TMap(TInteger);
        var emptyMap = JObject(new StringMap());
        var goodMap = JObject(["a" => JNumber(1), "b" => JNumber(1123)]);
        var badMap = JObject(["a" => JNumber(1), "b" => JNumber(1123.1)]);

        this.assertTrue(new Teleport().validate(s, emptyMap));
        this.assertTrue(new Teleport().validate(s, goodMap));
        this.assertFalse(new Teleport().validate(s, badMap));
    }

    public function testValidateStruct() {
        var s = this.structSchema;

        this.assertTrue(new Teleport().validate(s, JsonTools.parseUnsafe('{"name": "Alexei"}')));
        this.assertTrue(new Teleport().validate(s, JsonTools.parseUnsafe('{"name": "Alexei", "age": 24}')));
        this.assertFalse(new Teleport().validate(s, JsonTools.parseUnsafe('{"name": 1, "age": 24}')));
        this.assertFalse(new Teleport().validate(s, JsonTools.parseUnsafe('{"name": "Alexei", "age": null}')));
    }

    public function testValidateStructAlt() {
        var s = this.structSchema;

        this.assertTrue(new Teleport().validate(s, JsonTools.parseUnsafe('{"name": "Alexei"}')));
        this.assertTrue(new Teleport().validate(s, JsonTools.parseUnsafe('{"name": "Alexei", "age": 24}')));
        this.assertFalse(new Teleport().validate(s, JsonTools.parseUnsafe('{"name": 1, "age": 24}')));
        this.assertFalse(new Teleport().validate(s, JsonTools.parseUnsafe('{"name": "Alexei", "age": null}')));
    }

    public function testValidateRfc3999() {
        Util.parseRfc3999('1985-04-12T23:20:50.52Z');
        Util.parseRfc3999('1985-04-12T23:20:50Z');
        Util.parseRfc3999('1985-04-12T23:20:50+00:01');
        this.assertTrue(true);
    }

}