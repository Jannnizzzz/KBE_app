
from parapy.core import Base, Input, Attribute, Part

class Motor(Base):
    torque_op = Input()
    rpm_op = Input()

    @Attribute
    def kv(self):
        return 0

    @Attribute
    def ra(self):
        return 0