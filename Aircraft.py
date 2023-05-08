
from parapy.core import *
from parapy.exchange import STEPWriter
from parapy.geom.generic.positioning import Point
from Wing import Semiwing
from Battery import Battery
from Engine import Engine
from Payload import Payload
from __init__ import generate_warning
from Fuselage import Fuselage

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Aircraft(Base):
    # main input parameters
    endurance = Input()             # endurance time (in h) or range (in km) for design
    endurance_mode = Input()        # either 'T' for time or 'R' for range
    velocity = Input()              # design velocity (in km/h)
    propeller = Input()             # propeller used (format 'DxH', in inch)
    num_engines = Input()           # number of separate engines (propeller-motor-pair)
    structural_material = Input()
    airfoil_root = Input()          # name of the airfoil of the wings root
    airfoil_tip = Input()           # name of the airfoil of the wings root

    # maximum dimensions of the drone
    max_width = Input(3)            # maximum wing span (in m)
    max_length = Input(3)           # maximum length (in m)
    max_height = Input(0.2)         # maximum height (in m)

    # payload dimensions
    payload_width   = Input(0.2)    # in m
    payload_length  = Input(0.5)    # in m
    payload_height  = Input(0.2)    # in m
    payload_weight  = Input(2.0)    # in kg

    wing_surface_area   = 1         #dummy value
    tail_cl     = 0.0               #as it should be symmetric
    cl_required = Input(0.4)

    air_density = Input(1.225)

    # battery parameters (initial value, to be changed during iteration)
    battery_capacity = Input(1)
    battery_cells = Input(3)

    #__initargs__ = "endurance, endurance_mode, velocity, propeller, num_engines"# , structural_material, " \
                   # + "airfoil_root, airfoil_tip"


    @Attribute
    def time_requirement(self):
        return self.endurance if self.endurance_mode == 'T' else self.endurance / self.velocity

    @Input
    def prop_diameter(self):
        split = self.propeller.index('x')
        return int(self.propeller[:split]) * 0.0254

    @Input
    def prop_pitch(self):
        split = self.propeller.index('x')
        return int(self.propeller[split+1:])

    @Attribute
    def is_valid(self):
        valid = True
        for i in range(self.num_engines):
            engine_valid = self.engines[i].motor.is_valid
            propeller_valid = self.engines[i].propeller.op_valid
            valid = valid and engine_valid and propeller_valid
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

        # COG influence of the battery
        cog_x += self.battery.cog.x * self.battery.weight
        cog_y += self.battery.cog.y * self.battery.weight
        cog_z += self.battery.cog.z * self.battery.weight

        # COG influence of the payload
        cog_x += self.payload.cog.x * self.payload.weight
        cog_y += self.payload.cog.y * self.payload.weight
        cog_z += self.payload.cog.z * self.payload.weight

        # COG influence of the engines
        for i in range(self.num_engines):
            cog_x += self.engines[i].cog.x * self.engines[i].weight
            cog_y += self.engines[i].cog.y * self.engines[i].weight
            cog_z += self.engines[i].cog.z * self.engines[i].weight


        # final COG calculation
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

    @Attribute
    def battery_cells_required(self):
        cells = np.NaN
        for i in range(self.num_engines):
            cells = np.nanmin([cells, self.engines[i].motor.battery_cells_required])
        return cells.astype(int)

    @Attribute
    def motor_data(self):
        data = pd.read_excel('Motor_data.xlsx')
        data = np.array(data)
        data = data[data[:, 1].argsort()]
        return data

    @Attribute
    def drag(self):
        drag = 0

        # wing drag
        cD = self.wing.wing_cd
        air_density = self.air_density
        velocity = self.velocity/3.6    # in m/s
        surface = 1                     # dummy value for now
        drag += air_density/2 * velocity**2 * surface * cD

        # TODO: drag of other components

        return drag

    @Attribute
    def motor_y_positions(self):
        y_pos = np.zeros((self.num_engines,))
        fuselage_radius = max(self.fuselage.battery_section_radius, self.fuselage.payload_section_radius)

        if self.num_engines % 2 == 1:
            middle_index = int((self.num_engines-1)/2)
            y_pos[middle_index] = 0

            y_pos[middle_index + 1] = max(fuselage_radius + 3/4*self.prop_diameter, 3/2*self.prop_diameter)
            y_pos[middle_index - 1] = -max(fuselage_radius + 3/4*self.prop_diameter, 3/2*self.prop_diameter)
            for i in range(2, self.num_engines - middle_index):
                y_pos[middle_index + i] = y_pos[middle_index + i - 1] + 3/2*self.prop_diameter
                y_pos[middle_index - i] = y_pos[middle_index - i + 1] - 3/2*self.prop_diameter

        else:
            halve_point = int(self.num_engines/2)
            y_pos[halve_point] = max(fuselage_radius + 3/4*self.prop_diameter, 3/4*self.prop_diameter)
            y_pos[halve_point-1] = -max(fuselage_radius + 3/4*self.prop_diameter, 3/4*self.prop_diameter)

            for i in range(1, halve_point):
                y_pos[halve_point + i] = y_pos[halve_point + i - 1] + 3/2*self.prop_diameter
                y_pos[halve_point - i - 1] = y_pos[halve_point + i - 2] - 3/2*self.prop_diameter

        return y_pos

    @Part
    def battery(self):
        return Battery(cap=self.battery_capacity,
                       cells=self.battery_cells)

    @Part
    def wing(self):
        return Semiwing(airfoil_root=self.airfoil_root,
                        airfoil_tip=self.airfoil_tip,
                        cl=self.cl_required,
                        air_density=self.air_density)

    @Part
    def fuselage(self):
        return Fuselage()

    #@Part
    #def tail(self):
    #    return Tail()

    @Part
    def engines(self):
        return Engine(quantify=self.num_engines,
                      prop=self.propeller,
                      velocity_op=self.velocity,
                      thrust_op=self.drag/self.num_engines,
                      max_voltage=self.battery.voltage,
                      voltage_per_cell=self.battery.voltage_per_cell,
                      motor_data=self.motor_data,
                      pos_x=np.sign((self.num_engines-1)/2 - child.index) * np.tan(np.radians(self.wing.sweep))
                            * self.motor_y_positions[child.index] if child.index != (self.num_engines-1)/2
                            else self.fuselage.profile_set[0].location.x,
                      pos_y=self.motor_y_positions[child.index],
                      pos_z=0 if child.index != (self.num_engines-1)/2
                              else self.fuselage.profile_set[0].location.z,
                      iteration_history=np.zeros((3,)))

    @Part
    def payload(self):
        return Payload(length=self.payload_length,
                       width=self.payload_width,
                       height=self.payload_height,
                       weight=9.80665*self.payload_weight,
                       cog_x=self.battery.cog.x-self.battery.length/2-self.payload_length/2,
                       cog_y=0,
                       cog_z=0)

    #@Part
    #def fuselage(self):
    #    return Fuselage()

    @Part
    def step_writer(self):
        return STEPWriter(trees=[self], filename="Outputs/step_export.stp", unit="M")

    @action
    def iterate(self):
        any_changes = True

        while any_changes:
            print("=================================")
            print("Total mass", self.total_weight/9.80665, " kg")
            print("Capacity", self.battery.capacity, " Ah")
            any_changes = False

            # change the required cL of the wing to match current conditions
            self.cl_required = self.total_weight/(self.wing_surface_area*0.5*self.air_density*self.velocity**2)

            # calculate, if the surface area of the wing has to be changed
            required_extra_area = self.total_weight-(self.wing_surface_area*self.air_density*self.cl_required*0.5*self.velocity**2)/(self.air_density*self.cl_required*0.5*self.velocity**2)
            if abs(required_extra_area) >= 0.1:
                print("Change surface area")
                any_changes = True
                self.wing_surface_area += required_extra_area

            # adjust motor selection
            for i in range(self.num_engines):
                change = self.engines[i].iterate
                if change:
                    print("Change motor")
                any_changes = any_changes or change

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

    @action
    def create_prop_curve(self):
        characteristics, _ = self.engines[0].propeller.prop_characteristics
        v, t = characteristics[:, 0, :], self.num_engines*characteristics[:, 7, :]

        plt.plot(v, t, 'b')
        plt.plot(self.velocity, self.drag, 'r*')
        plt.plot([0, self.velocity, self.velocity], [self.drag, self.drag, 0], 'k:')
        plt.xlabel("Velocity (km/h)")
        plt.ylabel("Thrust (N)")
        plt.title("Thrust over velocity of the drone")
        plt.savefig('Outputs/prop_curves.pdf')
        plt.close()

    @action
    def create_motor_curve(self):
        characteristics, rpm = self.engines[0].propeller.prop_characteristics
        v, q = characteristics[:, 0, :], characteristics[:, 6, :]
        rpm_matrix = np.ones((characteristics.shape[0], 1)) * rpm

        k_phi = self.engines[0].motor.k_phi
        resistance = self.engines[0].motor.resistance
        max_voltage = self.engines[0].motor.max_voltage

        motor_speed = np.array([0, max_voltage/k_phi])
        torque = (max_voltage/k_phi - motor_speed) / (resistance * 2*np.pi/k_phi**2)

        plt.plot(torque, motor_speed)
        sc = plt.scatter(q, rpm_matrix/60, s=2, c=v)
        plt.plot(self.engines[0].propeller.torque_op, self.engines[0].propeller.rpm_op/60, "r*")
        plt.plot([0, self.engines[0].propeller.torque_op, self.engines[0].propeller.torque_op],
                 [self.engines[0].propeller.rpm_op/60, self.engines[0].propeller.rpm_op/60, 0], 'k:')
        plt.colorbar(sc, label="Velocity (km/h)")
        plt.xlabel("Motor Torque (Nm)")
        plt.ylabel("Motor Speed (1/s)")
        plt.title("Motor Characteristics for max. Voltage\n and Propeller Torque Requirement")
        plt.savefig('Outputs/motor_curves.pdf')
        plt.close()

    @action
    def velocity_sweep(self):
        velocity = np.linspace(50, 150, 10)
        drag = 0.05 * (velocity/3.6)**2
        motor_speed, torque, thrust, voltage, current, op_valid = self.engines[0].variable_velocity(velocity, drag/self.num_engines)

        plt.plot(velocity, motor_speed)
        plt.xlabel("Velocity (km/h)")
        plt.ylabel("Motor Speed (1/s)")
        plt.title("")
        plt.savefig('Outputs/velocity_sweep.pdf')
        plt.close()




if __name__ == '__main__':
    data = pd.read_excel('Input_data.xlsx')
    data = np.array(data)

    obj = Aircraft(endurance=data[0, 1],
                   endurance_mode=data[1, 1],
                   velocity=data[2, 1],
                   propeller=data[3, 1],
                   num_engines=data[4, 1],
                   structural_material=data[5, 1],
                   airfoil_root=data[6, 1],
                   airfoil_tip=data[7, 1])

    from parapy.gui import display

    #obj.iterate()
    obj.velocity_sweep()
    display(obj)
