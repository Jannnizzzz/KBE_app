
from parapy.core import Base, Input, Attribute, Part
from Propeller import Propeller
from Motor import Motor

class Engine(Base):
    prop_diameter = Input()
    prop_inclination = Input()
    velocity_op = Input()
    thrust_op = Input()

    @Attribute
    def rpm_op(self):
        return self.propeller.rpm_op

    @Attribute
    def torque_op(self):
        return self.propeller.torque_op

    @Part
    def propeller(self):
        return Propeller(diameter=self.prop_diameter,
                         inclination=self.prop_inclination,
                         velocity_op=self.velocity_op,
                         thrust_op=self.thrust_op)

    @Part
    def motor(self):
        return Motor(torque_op=self.torque_op, rpm_op=self.rpm_op)
