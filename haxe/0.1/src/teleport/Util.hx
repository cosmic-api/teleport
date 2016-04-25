package teleport;

import haxe.ds.Option;
import haxe.ds.Either;


typedef DateTime = {
    var year:Int;
    var month:Int;
    var day:Int;
    var hour:Int;
    var minute:Int;
    var second:Int;
    var millisecond:Option<Float>;
    var offset:Option<Int>;
}


class Util {
    public static function parseRfc3999(s:String):Option<DateTime> {
        var regex = ~/^(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(\.\d+)?Z|((\+|-)(\d\d):(\d\d))$/;
        var millisecond, offset;

        regex.match(s);
        var year = Std.parseInt(regex.matched(1));
        var month = Std.parseInt(regex.matched(2));
        var day = Std.parseInt(regex.matched(3));

        var hour = Std.parseInt(regex.matched(4));
        var minute = Std.parseInt(regex.matched(5));
        var second = Std.parseInt(regex.matched(6));

        var frac = regex.matched(7);
        if (frac == null) {
            millisecond = None;
        } else {
            millisecond = Some(Std.parseFloat('0' + frac));
        }

        if (regex.matched(8) == null) {
            offset = None;
        } else {
            var sign = if (regex.matched(9) == '+') 1 else -1;
            var hoursOffset = Std.parseInt(regex.matched(10));
            var minutesOffset = Std.parseInt(regex.matched(11));
            offset = Some(sign * (hoursOffset * 60 + minutesOffset));
        }

        return Some({
            year: year,
            month : month,
            day : day,
            hour : hour,
            minute : minute,
            second : second,
            millisecond : millisecond,
            offset : offset
        });
    }

    public static function isValidRfc3339(s:String):Bool {
        return true;
    }
}

