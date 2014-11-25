import re

from teleport import Teleport, ConcreteType

t = Teleport()

@t.register("Color")
class ColorType(ConcreteType):

    def contains(self, value):
        if not t("String").contains(value):
            return False
        return re.compile('^#[0-9a-f]{6}$').match(value) is not None
