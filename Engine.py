
from parapy.core import Base, Input, Attribute, Part
from Propeller import Propeller
from parapy.geom.generic.positioning import Point, Vector
from parapy.core.validate import IsInstance
from Motor import Motor

class Engine(Base):
    prop = Input()
    velocity_op = Input()
    thrust_op = Input()
    max_voltage = Input()
    voltage_per_cell = Input()
    motor_data = Input()
    cog = Input(Point(0, 0, 0), validator=IsInstance(Point))

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
        return Propeller(pass_down="prop, velocity_op",
                         thrust=self.thrust_op,
                         position=self.cog+Vector(self.motor.length, 0, 0))

    @Part
    def motor(self):
        return Motor(pass_down="torque_op, speed_op, voltage_per_cell, motor_data, cog")
