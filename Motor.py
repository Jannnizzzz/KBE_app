
from parapy.core import Base, Input, Attribute, Part
import numpy as np

class Motor(Base):
    torque_op = Input()
    speed_op = Input()
    max_voltage = Input()
    voltage_per_cell = Input()
    max_current = Input(20)
    resistance = Input(.025)
    kv_init = Input(2200)             # in RPM/V

    @Input
    def k_phi(self):
        #return 60/self.kv_init
        return max(np.sqrt(2*np.pi * self.resistance * self.torque_op / self.speed_op),
                   2 * np.pi / self.max_current * self.torque_op)

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
        return (self.current < self.max_current) and (self.voltage < self.max_voltage)

    @Attribute
    def battery_cells_required(self):
        characteristics, rpm = self.parent.propeller.prop_characteristics
        torque = characteristics[:, 6, :]
        voltages = np.zeros_like(torque)
        for i in range(voltages.shape[1]):
            voltages[:, i] = (rpm[i]/60 + 2 * np.pi * self.resistance / self.k_phi ** 2 * torque[:, i]) * self.k_phi

        return np.ceil(np.nanmax(voltages) / self.voltage_per_cell)