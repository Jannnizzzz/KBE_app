
from parapy.core import Base, Input, Attribute, Part
from parapy.geom import Cylinder
from parapy.geom.generic.positioning import Position, Point, Orientation
from parapy.core.validate import IsInstance
import numpy as np

class Motor(Base):
    torque_op = Input()
    speed_op = Input()
    max_voltage = Input()
    voltage_per_cell = Input()
    motor_data = Input()
    motor_idx = Input(0)
    cog = Input(validator=IsInstance(Point))

    @Attribute
    def k_phi(self):
        return 60/self.kV

    @Attribute
    def kV(self):
        return self.motor_data[self.motor_idx, 1]

    @Attribute
    def weight(self):
        return 9.80665 * self.motor_data[self.motor_idx, 7]/1000

    @Attribute
    def max_voltage(self):
        return self.motor_data[self.motor_idx, 6]

    @Attribute
    def max_current(self):
        return self.motor_data[self.motor_idx, 5]

    @Attribute
    def resistance(self):
        return self.motor_data[self.motor_idx, 2]

    @Attribute
    def voltage(self):
        return self.speed_op * self.k_phi + 2*np.pi * self.resistance / self.k_phi * self.torque_op

    def variable_voltage(self, speed, torque):
        return speed * self.k_phi + 2*np.pi * self.resistance / self.k_phi * torque

    @Attribute
    def current(self):
        return 2 * np.pi / self.k_phi * self.torque_op

    def variable_current(self, torque):
        return 2 * np.pi / self.k_phi * torque

    @Attribute
    def current_valid(self):
        return self.current <= self.max_current

    def variable_current_valid(self, torque):
        return self.variable_current(torque) <= self.max_current

    @Attribute
    def voltage_valid(self):
        return self.voltage <= self.parent.parent.battery.voltage

    def variable_voltage_valid(self, speed, torque):
        return self.variable_voltage(speed, torque) <= self.parent.parent.battery.voltage

    @Attribute
    def is_valid(self):
        return self.current_valid and self.voltage_valid

    def variable_valid(self, speed, torque):
        return self.variable_current_valid(torque) and self.variable_voltage_valid(speed, torque)

    @Attribute
    def voltages(self):
        characteristics, rpm = self.parent.propeller.prop_characteristics
        torque = characteristics[:, 6, :]
        voltages = np.zeros_like(torque)
        for i in range(voltages.shape[1]):
            voltages[:, i] = rpm[i] / 60 * self.k_phi + 2 * np.pi * self.resistance / self.k_phi * torque[:, i]
        return voltages

    @Attribute
    def battery_cells_required(self):
        return np.ceil(self.max_voltage / self.voltage_per_cell)

    @Attribute
    def gradient_max_voltage(self):
        characteristics, rpm = self.parent.propeller.prop_characteristics
        torque = characteristics[:, 6, :]
        idx = np.unravel_index(np.nanargmax(self.voltages), self.voltages.shape)

        return rpm[idx[1]]/60 - 2 * np.pi * self.resistance * torque[idx[0], idx[1]] / self.k_phi**2

    @Attribute
    def gradient_current(self):
        return - 2 * np.pi * self.torque_op / self.k_phi**2

    @Attribute
    def diameter(self):
        return self.motor_data[self.motor_idx, 4]/1000

    @Attribute
    def length(self):
        return self.motor_data[self.motor_idx, 3]/1000

    @Part(parse=False)
    def body(self):
        return Cylinder(self.diameter/2, self.length,
                        centered=True,
                        position=Position(self.cog, Orientation(x='y', y='z')))
