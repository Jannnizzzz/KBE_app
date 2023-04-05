
from parapy.core import Base, Input, Attribute, Part
from Propeller import Propeller
from Motor import Motor

class Engine(Base):
    prop_diameter = Input()
    prop_inclination = Input()
    velocity_op = Input()
    thrust_op = Input()
    max_voltage = Input()

    @Attribute
    def speed_op(self):
        return self.propeller.rpm_op/60

    @Attribute
    def torque_op(self):
        return self.propeller.torque_op

    @Attribute
    def current(self):
        return self.motor.current

    @Part
    def propeller(self):
        return Propeller(diameter=self.prop_diameter,
                         inclination=self.prop_inclination,
                         velocity_op=self.velocity_op,
                         thrust_op=self.thrust_op)

    @Part
    def motor(self):
        return Motor(torque_op=self.torque_op,
                     speed_op=self.speed_op,
                     max_voltage=self.max_voltage)
