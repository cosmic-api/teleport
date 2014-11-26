import re

from teleport import Teleport, ConcreteType, GenericType

t = Teleport()

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

    def contains(self, value):
        if value is None:
            return True
        return self.child.contains(value)
