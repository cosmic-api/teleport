import re
import pickle

from teleport import TypeMap, ConcreteType, GenericType, Undefined

t = TypeMap()


@t.register("Color")
class ColorType(ConcreteType):

    def contains(self, value):
        if not t("String").contains(value):
            return False
        return re.compile('^#[0-9a-f]{6}$').match(value) is not None


@t.register("Nullable")
class NullableType(GenericType):

    def process_param(self, param):
        self.child = self.t(param)

    def from_json(self, value):
        if value is None:
            return None
        return self.child.from_json(value)

    def to_json(self, value):
        if value is None:
            return None
        return self.child.to_json(value)


@t.register("PythonObject")
class PythonObjectType(ConcreteType):

    def from_json(self, json_value):
        if not t("String").contains(json_value):
            raise Undefined("PythonObject must be a string")
        try:
            return pickle.loads(json_value)
        except:
            raise Undefined("PythonObject could not be unpickled")

    def to_json(self, native_value):
        return pickle.dumps(native_value)


