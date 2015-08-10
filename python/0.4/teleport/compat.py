import sys
import platform
import decimal

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PYPY = platform.python_implementation() == 'PyPy'


def normalize_string(s):
    if PY2 and type(s) == str:
        try:
            return unicode(s)
        except UnicodeDecodeError:
            return None
    elif PY2 and type(s) == unicode:
        return s
    elif PY3 and type(s) == str:
        return s
    else:
        return None


def test_integer(i):
    if PY2 and type(i) in (int, long):
        return True
    if PY3 and type(i) == int:
        return True
    return False


def test_long(n):
    if PY2 and type(n) in (long, int, float, decimal.Decimal):
        return True
    if PY3 and type(n) in (int, float, decimal.Decimal):
        return True
    return False


