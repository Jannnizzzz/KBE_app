
from parapy.core import Base, Input, Attribute, Part
from Wing import Wing
from Battery import Battery
from Engine import Engine

import numpy as np

class Aircraft(Base):
    endurance = Input()
    endurance_mode = Input()
    wing_airfoil = Input()
    propeller = Input()
    materials = Input()
    battery_capacity = Input(5)
    battery_cells = Input(3)
    velocity = Input(100)
    num_engines = Input(1)
    max_dimensions = Input(3)

    @Input
    def prop_diameter(self):
        split = self.propeller.index('x')
        return int(self.propeller[:split])

    @Input
    def prop_inclination(self):
        split = self.propeller.index('x')
        return int(self.propeller[split+1:])

    @Attribute
    def total_weight(self):
        return 9.80665 * self.battery.weight

    @Attribute
    def endurance_time(self):
        current = 0
        for i in range(self.num_engines):
            current += self.engines[i].current
        return self.battery.capacity/current

    @Attribute
    def endurance_range(self):
        return self.velocity*self.endurance_time

    def iterate(self):
        factor_cap = self.endurance/self.endurance_time if self.endurance_mode == 'T' else self.endurance/self.endurance_range
        if abs(self.battery.capacity * (1 - factor_cap))/self.battery.capacity_per_cell > 1:
            self.battery_capacity *= factor_cap

        self.battery_cells = self.battery_cells_required

    @Attribute
    def battery_cells_required(self):
        cells = 0
        for i in range(self.num_engines):
            cells = np.max(self.engines[i].motor.battery_cells_required)
        return cells

    @Attribute
    def aerodynamic_efficiency(self):
        return .02
    @Attribute
    def thrust(self):
        return self.aerodynamic_efficiency * self.total_weight

    @Part
    def battery(self):
        return Battery(cap=self.battery_capacity,
                       cells=self.battery_cells)

    @Part
    def wing(self):
        return Wing()

    #@Part
    #def tail(self):
    #    return Tail()

    @Part
    def engines(self):
        return Engine(quantify=self.num_engines,
                      prop=self.propeller,
                      velocity_op=self.velocity,
                      thrust_op=self.thrust,
                      max_voltage=self.battery.voltage,
                      voltage_per_cell=self.battery.voltage_per_cell)

    #@Part
    #def payload(self):
    #    return Payload()

    #@Part
    #def fuselage(self):
    #    return Fuselage()

if __name__ == '__main__':
    obj = Aircraft(endurance=2,
                   endurance_mode='T',
                   wing_airfoil='NACA4206',
                   propeller='7x7',
                   materials='wood')

    from parapy.gui import display

    display(obj)