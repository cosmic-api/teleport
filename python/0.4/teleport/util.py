from __future__ import unicode_literals

from datetime import tzinfo, timedelta


class UTC(tzinfo):
    """Why is this not in the standard library?
    """
    ZERO = timedelta(0)

    def utcoffset(self, dt):
        return self.ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return self.ZERO

    def __repr__(self):
        return '<UTC>'

utc = UTC()


def ghetto_json_pointer(tup):
    return '/' + '/'.join(map(str, tup))


def format_multiple_errors(errors):
    ret = "\n"
    for message, location in errors:
        pointer = ghetto_json_pointer(location)

        ret += pointer
        if len(pointer) < 10:
            ret += ' ' * (10 - len(pointer))
        ret += message + '\n'
    return ret
