
from parapy.core import Base, Input, Attribute, Part
import numpy as np

class Motor(Base):
    torque_op = Input()
    speed_op = Input()
    max_voltage = Input()
    voltage_per_cell = Input()
    max_current = Input(20)
    resistance = Input(.025)
    kv = Input(180)

    @Attribute
    def voltage(self):
        return (60*self.speed_op + 2*np.pi * self.resistance * self.kv**2 * self.torque_op) / self.kv

    @Attribute
    def efficiency(self):
        return 1 - 2 * np.pi * self.resistance/self.voltage * self.kv * self.torque_op

    @Attribute
    def current(self):
        return 2 * np.pi * self.kv * self.torque_op

    @Attribute
    def is_possible(self):
        return (self.current < self.max_current) and (self.voltage < self.max_voltage)

    @Attribute
    def battery_cells_required(self):
        return np.ceil(self.voltage/self.voltage_per_cell)
