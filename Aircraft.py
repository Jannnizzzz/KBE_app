
from parapy.core import Base, Input, Attribute, Part, action
from Wing import Wing
from Battery import Battery
from Engine import Engine
from Payload import Payload

import numpy as np
import pandas as pd



class Aircraft(Base):
    endurance = Input()
    endurance_mode = Input()
    wing_airfoil = Input()
    propeller = Input()
    materials = Input()
    battery_capacity = Input(5)
    battery_cells = Input(3)
    velocity = Input(100)
    num_engines = Input(2)
    #adjust_num_engines = Input(False)
    max_dimensions = Input(3)

    @Attribute
    def time_requirement(self):
        return self.endurance if self.endurance_mode == 'T' else self.endurance / self.velocity

    @Input
    def prop_diameter(self):
        split = self.propeller.index('x')
        return int(self.propeller[:split])

    @Input
    def prop_inclination(self):
        split = self.propeller.index('x')
        return int(self.propeller[split+1:])

    @Attribute
    def is_valid(self):
        valid = True
        for i in range(self.num_engines):
            valid = valid and self.engines[i].motor.is_possible and self.engines[i].propeller.op_valid
        return valid

    @Attribute
    def total_weight(self):
        return self.battery.weight + self.payload.weight

    @Attribute
    def total_current(self):
        current = 0
        for i in range(self.num_engines):
            current += self.engines[i].current
        return current

    @Attribute
    def endurance_time(self):
        return self.battery.capacity/self.total_current

    @Attribute
    def endurance_range(self):
        return self.velocity*self.endurance_time

    @action
    def iterate(self):
        any_changes = True

        while any_changes:
            any_changes = False

            # max_voltage = [np.nanmax(self.engines[i].motor.voltages) for i in range(self.num_engines)]
            #             bool_max_voltage = (max_voltage == np.nanmax(max_voltage))
            #
            #             # W_bat ~= max_voltage/voltage_per_cell * current*time/capacity_per_cell
            #             # d W_bat/d kPhi = time/voltage_per_cell/capacity_per_cell *
            #             #                   (current * d max_voltage/d kPhi + max_voltage * d current/d kPhi)
            #             gradient = np.zeros((self.num_engines,))
            #             for i in range(self.num_engines):
            #                 # current gradient
            #                 dcurrent_dkphi = np.nanmax(max_voltage) * self.engines[i].motor.gradient_current
            #                 gradient[i] = 0 if dcurrent_dkphi > 0 and self.engines[i].motor.current > self.engines[i].motor.max_current\
            #                                 else dcurrent_dkphi
            #
            #                 # max voltage gradient
            #                 if bool_max_voltage[i]:
            #                     dvoltage_dkphi = self.total_current * self.engines[i].motor.gradient_max_voltage
            #                     gradient[i] += 0 if dvoltage_dkphi > 0 and self.engines[i].motor.current > self.engines[i].motor.max_current\
            #                                     else dvoltage_dkphi
            #
            #             #print(gradient)
            #             if np.max(np.abs(gradient)) > 10 or np.any(gradient == 0):
            #                 any_changes = True
            #                 print(-gradient/500000000)
            #                 for i in range(self.num_engines):
            #                     if gradient[i] != 0:
            #                         self.engines[i].motor.k_phi -= gradient[i] / 500000000
            #                     else:
            #                         self.engines[i].motor.k_phi = 2 * np.pi / self.engines[i].motor.max_current * self.engines[i].motor.torque_op


            factor_cap = self.endurance/self.endurance_time if self.endurance_mode == 'T'\
                                                            else self.endurance/self.endurance_range

            num_add_cells = np.ceil(self.battery.capacity * (factor_cap - 1)/self.battery.capacity_per_cell)
            if num_add_cells != 0:
                any_changes = True
                self.battery_capacity += num_add_cells * self.battery.capacity_per_cell

            if self.battery_cells != self.battery_cells_required:
                any_changes = True
                self.battery_cells = self.battery_cells_required

            print(self.total_weight)

    @Attribute
    def battery_cells_required(self):
        cells = 0
        for i in range(self.num_engines):
            cells = np.max([cells, self.engines[i].motor.battery_cells_required])
        return cells

    @Attribute
    def motor_data(self):
        WS = pd.read_excel('Motor_data.xlsx')
        return np.array(WS)

    @Attribute
    def thrust(self):
        # return self.aerodynamic_efficiency * self.total_weight
        surface = self.total_weight/55
        rho = 1.225
        cD0 = .02
        k = 1 / (np.pi * surface/self.max_dimensions**2 * .8)

        return 0.5 * rho * surface * cD0 * (self.velocity/3.6)**2 \
            + 2 * self.total_weight**2 * k / (rho * surface * (self.velocity/3.6)**2)

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
                      thrust_op=self.thrust/self.num_engines,
                      max_voltage=self.battery.voltage,
                      voltage_per_cell=self.battery.voltage_per_cell,
                      motor_data=self.motor_data)

    @Part
    def payload(self):
        return Payload(weight=9.80665*2)

    #@Part
    #def fuselage(self):
    #    return Fuselage()


if __name__ == '__main__':
    obj = Aircraft(endurance=2,
                   endurance_mode='T',
                   wing_airfoil='NACA4206',
                   propeller='10x3',
                   materials='wood')

    from parapy.gui import display

    display(obj)
