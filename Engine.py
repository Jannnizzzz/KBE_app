
from parapy.core import Base, Input, Attribute, Part
from Propeller import Propeller
from Motor import Motor

class Engine(Base):
    prop = Input()
    velocity_op = Input()
    thrust_op = Input()
    max_voltage = Input()
    voltage_per_cell = Input()
    motor_data = Input()
    motor_idx = Input()

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
                         thrust=self.thrust_op)

    @Part
    def motor(self):
        return Motor(pass_down="torque_op, speed_op, voltage_per_cell, motor_data, motor_idx")
