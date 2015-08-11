from __future__ import unicode_literals

import itertools

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

class IterableException(Exception):
    pass

class Undefined(IterableException):

    def __init__(self, message, location=()):
        self.message = message
        self.location = location

    def to_json(self):
        return OrderedDict([
            ("message", self.message),
            ("pointer", list(self.location))
        ])

    def prepend_location(self, item):
        return self.__class__(self.message, (item,) + self.location)

    def __iter__(self):
        return [self]


class ValidationError(IterableException):

    def __init__(self, generator):
        self.exceptions = generator

    def to_json(self):
        return [e.to_json() for e in self.exceptions]

    def __str__(self):
        tups = [(e.message, e.location) for e in self.exceptions]
        return format_multiple_errors(tups)
 
    def __iter__(self):
        return self.exceptions


class ForceReturn(Exception):
    """Not an error, return value from error iterator"""
    def __init__(self, value):
        self.value = value


class IncorrectErrorGenerator(Exception):
    pass


class ErrorGenerator(object):

    def __init__(self, f):
        setattr(self, 'f', f)

    def __call__(self, *args, **kwargs):
        try:
            gen = getattr(self, 'f')(*args, **kwargs)
            try:
                err = next(gen)
            except StopIteration:
                raise IncorrectErrorGenerator(
                    "No errors generated and no value returned")
            raise ValidationError(itertools.chain([err], gen))

        except ForceReturn as ret:
            return ret.value

def error_generator(f):

    def call(*args, **kwargs):
        try:
            gen = f(*args, **kwargs)
            try:
                err = next(gen)
            except StopIteration:
                raise IncorrectErrorGenerator(
                    "No errors generated and no value returned")
            raise ValidationError(itertools.chain([err], gen))

        except ForceReturn as ret:
            return ret.value

    return call