
from parapy.core import Base, Input, Attribute, Part
import numpy as np

class Motor(Base):
    torque_op = Input()
    speed_op = Input()
    max_voltage = Input()
    voltage_per_cell = Input()
    max_current = Input(40)
    resistance = Input(.025)
    k_phi = Input(60/2200)

    #@Input
    #def k_phi(self):
    #    return max(np.sqrt(2*np.pi * self.resistance * self.torque_op / self.speed_op),
    #               2 * np.pi / self.max_current * self.torque_op)

    @Input
    def kV(self):
        return 60/self.k_phi

    @Attribute
    def voltage(self):
        return self.speed_op * self.k_phi + 2*np.pi * self.resistance / self.k_phi * self.torque_op

    #@Attribute
    #def efficiency(self):
    #    return 1 - 2 * np.pi * self.resistance/self.voltage / self.k_phi * self.torque_op

    @Attribute
    def current(self):
        return 2 * np.pi / self.k_phi * self.torque_op

    @Attribute
    def is_possible(self):
        return (self.current <= self.max_current) and (self.voltage <= self.max_voltage)

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
        return np.ceil(np.nanmax(self.voltages) / self.voltage_per_cell)

    @Attribute
    def gradient_max_voltage(self):
        characteristics, rpm = self.parent.propeller.prop_characteristics
        torque = characteristics[:, 6, :]
        idx = np.unravel_index(np.nanargmax(self.voltages), self.voltages.shape)

        return rpm[idx[1]]/60 - 2 * np.pi * self.resistance * torque[idx[0], idx[1]] / self.k_phi**2

    @Attribute
    def gradient_current(self):
        return - 2 * np.pi * self.torque_op / self.k_phi**2
