
from parapy.core import Base, Input, Attribute, Part

class Propeller(Base):
    diameter = Input()
    inclination = Input()
    thrust_op = Input()
    velocity_op = Input()

    @Input
    def prop_characteristics(self):
        return 0

    @Attribute
    def rpm_op(self):
        return 7000

    @Attribute
    def torque_op(self):
        return .0166