
from parapy.core import Base, Input, Attribute, Part

class Propeller(Base):
    propeller = Input()
    thrust_op = Input()
    velocity_op = Input()

    @Input
    def prop_characteristics(self):
        with open('Prop_data/P' + self.propeller + '.dat') as file:
            lines = []
            for line in file.readlines():
                lines.append(line.strip())
        return lines

    @Attribute
    def rpm_op(self):
        return 7000

    @Attribute
    def torque_op(self):
        return .0166