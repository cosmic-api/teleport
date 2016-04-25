package teleport;

import teleport.test.ValidationTestCase;

import haxe.Json;
import haxe.unit.TestRunner;


class TestSuite {
    static function main() {
        var r = new TestRunner();

        r.add(new ValidationTestCase());
        r.run();
    }
}
