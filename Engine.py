
from parapy.core import Base, Input, Attribute, Part
from Propeller import Propeller
from parapy.geom.generic.positioning import Point, Vector
from parapy.core.validate import IsInstance
from Motor import Motor

import numpy as np


class Engine(Base):
    prop = Input()
    velocity_op = Input()
    thrust_op = Input()
    max_voltage = Input()
    voltage_per_cell = Input()
    motor_data = Input()
    pos_x = Input()
    pos_y = Input()
    pos_z = Input()
    iteration_history = Input()

    @Attribute
    def iterate(self):
        any_changes = False
        change = True
        last_change_direction = 0

        while change:
            change = False
            if (not self.motor.voltage_valid) and self.motor.current_valid\
                    and self.motor.motor_idx < self.motor_data.shape[0] - 1 and (not (last_change_direction < 0))\
                    and (not (self.iteration_history[1] > 0 > self.iteration_history[2])):
                change = True
                any_changes = True
                last_change_direction = 1
                self.motor.motor_idx += 1
            if not self.motor.current_valid and self.motor.voltage_valid and self.motor.motor_idx > 0 \
                    and not (last_change_direction > 0)\
                    and not (self.iteration_history[2] > 0 > self.iteration_history[1]):
                change = True
                any_changes = True
                last_change_direction = -1
                self.motor.motor_idx -= 1
            if not self.motor.current_valid and not self.motor.voltage_valid and self.motor.motor_idx > 0 \
                    and not (last_change_direction > 0) \
                    and self.motor_data[self.motor.motor_idx, 6] < self.motor_data[self.motor.motor_idx-1, 6]\
                    and not (self.iteration_history[2] > 0 > self.iteration_history[1]):
                change = True
                any_changes = True
                last_change_direction = -1
                self.motor.motor_idx -= 1

        self.iteration_history[0] = self.iteration_history[1]
        self.iteration_history[1] = self.iteration_history[2]
        self.iteration_history[2] = last_change_direction
        return any_changes

    @Input
    def cog(self):
        return Point(self.pos_x+self.motor.length/2, self.pos_y, self.pos_z)

    @Attribute
    def weight(self):
        return self.motor.weight

    @Attribute
    def speed_op(self):
        return self.propeller.rpm_op/60

    @Attribute
    def torque_op(self):
        return self.propeller.torque_op

    @Attribute
    def current(self):
        return self.motor.current

    def variable_velocity(self, velocity, drag):
        operation_points = np.zeros((velocity.shape[0], 2), dtype=int)
        op_valid = np.zeros_like(velocity, dtype=bool)
        motor_speed = np.zeros_like(velocity)
        torque = np.zeros_like(velocity)
        thrust = np.zeros_like(velocity)
        voltage = np.zeros_like(velocity)
        current = np.zeros_like(velocity)
        for i in range(velocity.shape[0]):
            # finding propellers operating point
            operation_points[i, :] = self.propeller.variable_operation_point(velocity[i], drag[i])
            op_valid[i] = self.propeller.variable_op_valid(velocity[i], drag[i])
            motor_speed[i] = self.propeller.variable_rpm_op(operation_points[i, :])/60
            torque[i] = self.propeller.variable_torque_op(operation_points[i, :])
            thrust[i] = self.propeller.variable_thrust_op(operation_points[i, :])

            # finding motors operating point
            voltage[i] = self.motor.variable_voltage(motor_speed[i], torque[i])
            current[i] = self.motor.variable_current(torque[i])
            op_valid[i] = op_valid[i] and self.motor.variable_valid(motor_speed[i], torque[i])

        return motor_speed, torque, thrust, voltage, current, op_valid

    @Part
    def propeller(self):
        return Propeller(pass_down="prop, velocity_op",
                         thrust=self.thrust_op,
                         position=self.cog+Vector(self.motor.length/2, 0, 0))

    @Part
    def motor(self):
        return Motor(pass_down="torque_op, speed_op, voltage_per_cell, motor_data, cog")
