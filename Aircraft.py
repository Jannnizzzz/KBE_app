
from parapy.core import *
from parapy.geom.generic.positioning import Point
from Wing import Wing
from Battery import Battery
from Engine import Engine
from Payload import Payload
from __init__ import generate_warning

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
    num_engines = Input(5)
    #adjust_num_engines = Input(False)
    max_dimensions = Input(3)

    @Attribute
    def time_requirement(self):
        return self.endurance if self.endurance_mode == 'T' else self.endurance / self.velocity

    @Input
    def prop_diameter(self):
        split = self.propeller.index('x')
        return int(self.propeller[:split]) * 0.0254

    @Input
    def prop_inclination(self):
        split = self.propeller.index('x')
        return int(self.propeller[split+1:])

    @Attribute
    def is_valid(self):
        valid = True
        for i in range(self.num_engines):
            valid = valid and self.engines[i].motor.is_valid and self.engines[i].propeller.op_valid
        return valid

    @Attribute
    def total_weight(self):
        motor_weight = 0
        for i in range(self.num_engines):
            motor_weight += self.engines[i].weight
        return self.battery.weight + self.payload.weight + motor_weight

    @Attribute
    def cog(self):
        cog_x, cog_y, cog_z = 0, 0, 0

        cog_x += self.battery.cog.x * self.battery.weight
        cog_y += self.battery.cog.y * self.battery.weight
        cog_z += self.battery.cog.z * self.battery.weight

        cog_x += self.payload.cog.x * self.payload.weight
        cog_y += self.payload.cog.y * self.payload.weight
        cog_z += self.payload.cog.z * self.payload.weight

        for i in range(self.num_engines):
            cog_x += self.engines[i].cog.x * self.engines[i].weight
            cog_y += self.engines[i].cog.y * self.engines[i].weight
            cog_z += self.engines[i].cog.z * self.engines[i].weight

        cog_x /= self.total_weight
        cog_y /= self.total_weight
        cog_z /= self.total_weight
        return Point(cog_x, cog_y, cog_z)

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

        # initialize flag to prevent endless switching of motors due to no fitting one
        last_motor_change_direction = np.zeros((self.num_engines,))
        while any_changes:
            print(self.total_weight/9.80665)
            any_changes = False

            # adjust motor selection
            for i in range(self.num_engines):
                motor = self.engines[i].motor
                if not motor.voltage_valid and motor.current_valid and motor.motor_idx < self.motor_data.shape[0]-1\
                        and not (last_motor_change_direction[i] < 0):
                    any_changes = True
                    last_motor_change_direction[i] = 1
                    self.engines[i].motor.motor_idx += 1
                if not motor.current_valid and motor.voltage_valid and motor.motor_idx > 0\
                        and not (last_motor_change_direction[i] > 0):
                    any_changes = True
                    last_motor_change_direction[i] = -1
                    self.engines[i].motor.motor_idx -= 1

            # calculate, if the capacity of the battery has to be changed
            factor_cap = self.endurance/self.endurance_time if self.endurance_mode == 'T'\
                                                            else self.endurance/self.endurance_range
            num_add_cells = np.ceil(self.battery.capacity * (factor_cap - 1)/self.battery.capacity_per_cell)
            if num_add_cells != 0:
                print("Change capacity")
                any_changes = True
                self.battery_capacity += num_add_cells * self.battery.capacity_per_cell

            # calculate, if the voltage of the battery has to be increased
            if self.battery_cells != self.battery_cells_required:
                print("Change voltage")
                any_changes = True
                self.battery_cells = self.battery_cells_required

        if not self.is_valid:
            msg = "The iteration result found is not valid."
            generate_warning("Iteration result invalid", msg)

    @Attribute
    def battery_cells_required(self):
        cells = np.NaN
        for i in range(self.num_engines):
            cells = np.nanmin([cells, self.engines[i].motor.battery_cells_required])
        return cells

    @Attribute
    def motor_data(self):
        data = pd.read_excel('Motor_data.xlsx')
        data = np.array(data)
        data = data[data[:, 1].argsort()]
        return data

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
                      motor_data=self.motor_data,
                      pos_x=0,
                      pos_y=-(self.num_engines-1)*3/4*self.prop_diameter + child.index * 3/2*self.prop_diameter,
                      pos_z=0 if child.index != (self.num_engines-1)/2 else self.prop_diameter*3/4)

    @Part
    def payload(self):
        return Payload(length=0.1,
                       width=0.1,
                       height=0.1,
                       weight=9.80665*2,
                       cog_x=self.battery.cog.x-self.battery.length/2-0.06,
                       cog_y=0,
                       cog_z=0)

    #@Part
    #def fuselage(self):
    #    return Fuselage()


if __name__ == '__main__':
    obj = Aircraft(endurance=1,
                   endurance_mode='T',
                   wing_airfoil='NACA4206',
                   propeller='9x4',
                   materials='wood')

    from parapy.gui import display

    display(obj)
