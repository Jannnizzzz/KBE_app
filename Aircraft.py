from parapy.core import *
from parapy.exchange import STEPWriter
from parapy.geom.generic.positioning import Point
from parapy.geom import *
from Wing import Semiwing
from Battery import Battery
from Engine import Engine
from Payload import Payload
from __init__ import generate_warning
from Fuselage import Fuselage
from math import *

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Aircraft(GeomBase):
    # main input parameters
    endurance = Input()  # endurance time (in h) or range (in km) for design
    endurance_mode = Input()  # either 'T' for time or 'R' for range
    velocity = Input()  # design velocity (in km/h)
    propeller = Input()  # propeller used (format 'DxH', in inch)
    num_engines = Input()  # number of separate engines (propeller-motor-pair)
    structural_material = Input()  # type of material to be used for the structural part

    # maximum dimensions of the drone
    max_width = Input(3)  # maximum wing span (in m)
    max_length = Input(3)  # maximum length (in m)
    max_height = Input(0.2)  # maximum height (in m)

    # payload dimensions
    payload_width = Input(0.2)  # in m
    payload_length = Input(0.5)  # in m
    payload_height = Input(0.2)  # in m
    payload_weight = Input(2.0*9.80665)  # in N

    # geometry options

    wing_location = Input()                 # 0 for low wing, 1 for high wing, mid wing is not considered as it clashes with payload
    tail_location = Input()                 # 0 for low tail, 1 for T-tail

    # fuselage dimensions

    # wing dimensions & parameters
    skin_friction_coefficient = Input(0.0030)
    max_cl          = Input(1.0)
    stall_speed     = Input(50)                        #stall speed in km/h
    wing_surface_area = Input(1)  # dummy value
    n_ult           = Input(3.0)
    airfoil_root = Input()  # name of the airfoil of the wings root
    airfoil_tip = Input()  # name of the airfoil of the wings root

    cl_required = Input(0.4)


    t_factor_root = Input(1.0)
    t_factor_tip = Input(1.0)

    w_semi_span = Input(1.5)
    sweep = Input(5)
    twist = Input(2)
    incidence = Input(3)

    dynamic_viscosity = Input(1.8 * 10 ** (-5))
    air_density = Input(1.225)

    # horizontal tail section parameters

    tail_cl = Input(0.0)  #

    horizontal_tail_volume = Input(0.4)

    horizontal_tail_airfoil_root    = Input("whitcomb")
    horizontal_tail_airfoil_tip    = Input("whitcomb")

    horizontal_tail_t_factor_root = Input(1.0)
    horizontal_tail_t_factor_tip = Input(1.0)

    horizontal_tail_w_semi_span = Input(0.5)
    horizontal_tail_sweep = Input(10)
    horizontal_tail_twist = Input(2)
    horizontal_tail_incidence = Input(3)

    # vertical tail section parameters

    vertical_tail_volume = Input(0.4)

    vertical_tail_airfoil_root    = Input("whitcomb")
    vertical_tail_airfoil_tip    = Input("whitcomb")

    vertical_tail_t_factor_root = Input(1.0)
    vertical_tail_t_factor_tip = Input(1.0)

    vertical_tail_w_semi_span = Input(1.0)
    vertical_tail_sweep = Input(25)
    vertical_tail_twist = Input(2)
    vertical_tail_incidence = Input(3)

    #:
    wing_dihedral: float = Input(3)

    #: longitudinal position w.r.t. fuselage length. (% of fus length)
    wing_position_fraction_long: float = Input(0.3)

    #: vertical position w.r.t. to fus  (% of fus radius)
    wing_position_fraction_vrt: float = Input(0.8)

    #: longitudinal position of the vertical tail, as % of fus length
    vt_long: float = Input(0.6)

    #:
    vt_taper: float = Input(0.4)

    # battery parameters (initial value, to be changed during iteration)
    battery_capacity = Input(1)
    battery_cells = Input(3)

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
        return int(self.propeller[split + 1:])

    @Attribute
    def is_valid(self):
        valid = True
        for i in range(self.num_engines):
            engine_valid = self.engines[i].motor.is_valid
            propeller_valid = self.engines[i].propeller.op_valid
            valid = valid and engine_valid and propeller_valid
        return valid

    @Attribute
    def prelim_weight(self):
        motor_weight = 0
        for i in range(self.num_engines):
            motor_weight += self.engines[i].weight
        return 1.5*(self.battery.weight + self.payload.weight + motor_weight)

    # @Attribute  #based on stall speed for small propeller planes according to CS23
    # def wing_surface_area(self):
    #     print("Calculate wing area")
    #     return(self.prelim_weight/(0.5*self.max_cl*self.air_density*(self.stall_speed/3.6)**2))

    # @Attribute
    # def cl_required(self):
    #     return 1.1* self.prelim_weight / (self.wing_surface_area * 0.5 * self.air_density * self.velocity ** 2)

    @Attribute
    def aspect_ratio(self):
        return self.w_semi_span**2 / self.wing_surface_area

    @Attribute
    def wing_weight(self): #based on Roskam Cessna method with conversion from metric to imperial and back to metric
        return 0.4501*0.04674*((self.prelim_weight/0.4501)**(0.397))*((self.wing_surface_area/(0.3048**2))**0.360)*(self.n_ult**0.397)*(self.aspect_ratio**1.712)

    @Attribute
    def fuselage_weight(self): #based on Torenbeek method
        return(self.prelim_weight*(0.447*sqrt(self.n_ult)*((self.fuselage.fuselage_length*self.fuselage.payload_section_radius**2)/self.prelim_weight)**0.24))

    @Attribute
    def motor_weight(self):
        motor_weight = 0
        for i in range(self.num_engines):
            motor_weight += self.engines[i].weight
        return motor_weight

    @Attribute
    def total_weight(self):
        return self.battery.weight + self.payload.weight + self.motor_weight + self.wing_weight + self.fuselage_weight


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
        return self.battery.capacity / self.total_current

    @Attribute
    def endurance_range(self):
        return self.velocity * self.endurance_time

    @Attribute
    def battery_cells_required(self):
        cells = np.NaN
        for i in range(self.num_engines):
            cells = np.nanmin([cells, self.engines[i].motor.battery_cells_required])
        return cells.astype(int)

    @Attribute
    def motor_data(self):
        data = pd.read_excel('Inputs/Motor_data.xlsx')
        data = np.array(data)
        data = data[data[:, 1].argsort()]
        return data

    @Attribute
    def drag(self):
        print("Calculate drag")
        drag = 0
        velocity = self.velocity        # in km/h

        # wing drag
        cD_wing = self.right_wing.wing_cd
        drag += self.air_density/2 * (velocity/3.6)**2 * self.wing_surface_area * cD_wing

        # horizontal tail
        cD_htail = self.tail_right_wing.wing_cd
        drag += self.air_density/2 * (velocity/3.6)**2 * self.horizontal_tail_surface_area * cD_htail

        # horizontal tail
        cD_vtail = self.vertical_tail.wing_cd
        drag += self.air_density/2 * (velocity/3.6)**2 * self.vertical_tail_surface_area * cD_vtail

        # fuselage
        drag += self.zero_lift_drag

        return drag

    def variable_drag(self, velocities):
        drags = np.zeros_like(velocities)
        cLs = np.zeros_like(velocities)
        cDs = np.zeros_like(velocities)

        for i, velocity in enumerate(velocities):
            # wing drag
            cLs[i] = self.total_weight/(self.wing_surface_area*0.5*self.air_density*(velocity/3.6)**2)
            cDs[i] = self.right_wing.variable_wing_cd(velocity, cLs[i])
            drags[i] += self.air_density/2 * (velocity/3.6)**2 * self.wing_surface_area * cDs[i]

            # TODO: drag of other components

        return drags, cLs, cDs

    @Attribute
    def motor_y_positions(self):
        y_pos = np.zeros((self.num_engines,))
        fuselage_radius = self.fuselage.payload_section_radius

        if self.num_engines % 2 == 1:
            middle_index = int((self.num_engines-1)/2)
            y_pos[middle_index] = 0

            if self.num_engines > 1:
                y_pos[middle_index + 1] = max(fuselage_radius + self.prop_diameter, 3/2*self.prop_diameter)
                y_pos[middle_index - 1] = -max(fuselage_radius + self.prop_diameter, 3/2*self.prop_diameter)
                for i in range(2, self.num_engines - middle_index):
                    y_pos[middle_index + i] = y_pos[middle_index + i - 1] + 3/2*self.prop_diameter
                    y_pos[middle_index - i] = y_pos[middle_index - i + 1] - 3/2*self.prop_diameter

        else:
            halve_point = int(self.num_engines/2)
            y_pos[halve_point] = max(fuselage_radius + self.prop_diameter, 3/4*self.prop_diameter)
            y_pos[halve_point-1] = -max(fuselage_radius + self.prop_diameter, 3/4*self.prop_diameter)

            for i in range(1, halve_point):
                y_pos[halve_point + i] = y_pos[halve_point + i - 1] + 3/2*self.prop_diameter
                y_pos[halve_point - i - 1] = y_pos[halve_point + i - 2] - 3/2*self.prop_diameter

        return y_pos


    @Part
    def battery(self):
        return Battery(cap=self.battery_capacity,
                       cells=self.battery_cells)

    @Part
    def fuselage(self):
        return Fuselage(position= translate
                                        (self.position, "x",
                                         self.fuselage.payload_section_length/2,))


    @Part
    def rectangle(self):
        return Rectangle(width=1.0 * self.fuselage.payload_section_radius,
                         length=5.0 * child.width,
                         position=translate(
                             rotate90(self.position, 'z'),
                             # self.right_wing.position,
                             'y',
                             -0.1*self.fuselage.payload_section_length,
                             #'z', child.length * self.dist),

                         #hidden=True
                                  ))

    @Part
    def payload_door(self):
        return ProjectedCurve(source=self.rectangle,  # source
                              target=self.fuselage.fuselage_lofted_surf,  # target
                              direction=self.position.Vz)

    @Part
    def engines(self):
        return Engine(quantify=self.num_engines,
                      prop=self.propeller,
                      velocity_op=self.velocity,
                      thrust_op=self.drag/self.num_engines,
                      max_voltage=self.battery.voltage,
                      voltage_per_cell=self.battery.voltage_per_cell,
                      motor_data=self.motor_data,
                      pos_x=np.sign((self.num_engines-1)/2 - child.index) * np.tan(np.radians(self.right_wing.sweep))
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
                       weight=self.payload_weight,
                       cog_x=self.battery.cog.x - self.battery.length / 2 - self.payload_length / 2,
                       cog_y=0,
                       cog_z=0)

    @Part
    def right_wing(self):
        return Semiwing(airfoil_root=self.airfoil_root,
                        airfoil_tip=self.airfoil_tip,
                        wing_surface_area = self.wing_surface_area,

                        t_factor_root=self.t_factor_root,
                        t_factor_tip=self.t_factor_tip,

                        w_semi_span=self.w_semi_span,
                        sweep=self.sweep,
                        twist=self.twist,
                        incidence=self.incidence,

                        dynamic_viscosity=self.dynamic_viscosity,
                        air_density=self.air_density,
                        velocity=self.velocity,

                        cl=self.cl_required,

                        visc_option=1,

                        #position=rotate(
                        #                "x",
                        #                radians(self.wing_dihedral + 5)),
                        )


    @Part
    def left_wing(self):
        return MirroredShape(shape_in=self.right_wing,
                             reference_point=self.position,
                             # Two vectors to define the mirror plane
                             vector1=self.position.Vz,
                             vector2=self.position.Vx,
                             mesh_deflection=0.0001)

    @Attribute
    def tail_arm(self):
        return self.fuselage.fuselage_length * (self.vt_long - self.wing_position_fraction_long)

    @Attribute
    def horizontal_tail_surface_area(self):
        return ((self.horizontal_tail_volume*self.wing_surface_area*self.right_wing.mean_aerodynamic_chord)/self.tail_arm)

    @Attribute
    def vertical_tail_surface_area(self):
        return ((self.vertical_tail_volume*self.wing_surface_area*self.w_semi_span)/self.tail_arm)

    @Part
    def tail_right_wing(self):
        return Semiwing(airfoil_root=self.horizontal_tail_airfoil_root,
                        airfoil_tip=self.horizontal_tail_airfoil_tip,
                        wing_surface_area = self.horizontal_tail_surface_area,
                        t_factor_root=self.horizontal_tail_t_factor_root,
                        t_factor_tip=self.horizontal_tail_t_factor_tip,

                        w_semi_span=self.horizontal_tail_w_semi_span,
                        twist=self.horizontal_tail_twist,
                        incidence=self.horizontal_tail_incidence,

                        dynamic_viscosity=self.dynamic_viscosity,
                        air_density=self.air_density,
                        velocity=self.velocity,

                        cl=self.tail_cl,

                        visc_option=1,

                        position=rotate(translate
                                        (self.position, "x",
                                          -self.vt_long * self.fuselage.fuselage_length),
                                        "x",
                                        radians(self.wing_dihedral + 5)),
                        )

    @Part
    def tail_left_wing(self):
        return MirroredShape(shape_in=self.tail_right_wing,
                             reference_point=self.position,
                             # Two vectors to define the mirror plane
                             vector1=self.position.Vz,
                             vector2=self.position.Vx,
                             mesh_deflection=0.0001)

    @Part
    def vertical_tail(self):
        return Semiwing(airfoil_root=self.vertical_tail_airfoil_root,
                        airfoil_tip=self.vertical_tail_airfoil_tip,
                        wing_surface_area = self.vertical_tail_surface_area,
                        t_factor_root=self.vertical_tail_t_factor_root,
                        t_factor_tip=self.vertical_tail_t_factor_tip,

                        w_semi_span=self.vertical_tail_w_semi_span,
                        sweep=self.vertical_tail_sweep,
                        twist=self.vertical_tail_twist,
                        incidence=self.vertical_tail_incidence,

                        dynamic_viscosity=self.dynamic_viscosity,
                        air_density=self.air_density,
                        velocity=self.velocity,

                        cl=self.tail_cl,

                        visc_option=1,

                        position=rotate(translate
                                        (self.position,
                                         "x", -self.vt_long * self.fuselage.fuselage_length,
                                         "z", self.fuselage.tail_radius * 0.7),
                                        "x",
                                        radians(90)),
                        )

    @Part
    def step_writer(self):
        return STEPWriter(trees=[self], filename="Outputs/step_export.stp")

    @Attribute
    def zero_lift_drag(self):
        return self.skin_friction_coefficient * (self.fuselage.fuselage_lofted_surf.area+self.right_wing.area*2+self.tail_right_wing.area*2+self.vertical_tail.area)/self.wing_surface_area

    @action
    def iterate(self):
        any_changes = True

        while any_changes:
            print("=================================")
            print("Total mass", self.total_weight / 9.80665, " kg")
            print("Capacity", self.battery.capacity, " Ah")
            any_changes = False

            # change the required cL of the wing to match current conditions
            self.cl_required = self.total_weight/(self.wing_surface_area*0.5*self.air_density*(self.velocity/3.6)**2)

            # calculate, if the surface area of the wing has to be changed
            self.wing_surface_area = self.total_weight/(0.5*self.max_cl*self.air_density*(self.stall_speed/3.6)**2)

            # adjust motor selection
            for i in range(self.num_engines):
                change = self.engines[i].iterate
                if change:
                    print("Change motor")
                any_changes = any_changes or change

            # calculate, if the capacity of the battery has to be changed
            factor_cap = self.endurance / self.endurance_time if self.endurance_mode == 'T' \
                else self.endurance / self.endurance_range
            num_add_cells = np.ceil(self.battery.capacity * (factor_cap - 1) / self.battery.capacity_per_cell)
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
        v, t = characteristics[:, 0, :], self.num_engines * characteristics[:, 7, :]

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

        motor_speed = np.array([0, max_voltage / k_phi])
        torque = (max_voltage / k_phi - motor_speed) / (resistance * 2 * np.pi / k_phi ** 2)

        plt.plot(torque, motor_speed)
        sc = plt.scatter(q, rpm_matrix / 60, s=2, c=v)
        plt.plot(self.engines[0].propeller.torque_op, self.engines[0].propeller.rpm_op / 60, "r*")
        plt.plot([0, self.engines[0].propeller.torque_op, self.engines[0].propeller.torque_op],
                 [self.engines[0].propeller.rpm_op / 60, self.engines[0].propeller.rpm_op / 60, 0], 'k:')
        plt.colorbar(sc, label="Velocity (km/h)")
        plt.xlabel("Motor Torque (Nm)")
        plt.ylabel("Motor Speed (1/s)")
        plt.title("Motor Characteristics for max. Voltage\n and Propeller Torque Requirement")
        plt.savefig('Outputs/motor_curves.pdf')
        plt.close()

    @action
    def velocity_sweep(self):
        velocities = np.linspace(50, 150, 11)
        drags = self.variable_drag(velocities)
        motor_speed, torque, thrust, voltage, current, op_valid = self.engines[0].variable_velocity(velocities, drags/self.num_engines)

        fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(4, 1, sharex=True, sharey=False)
        ax1.plot(velocities, motor_speed)
        ax1.set_ylabel("Motor Speed (1/s)")
        ax1.set_title("")

        ax2.plot(velocities, drags)
        ax2.set_ylabel("Drag (N)")
        ax2.set_title("")

        ax3.plot(velocities, current)
        ax3.set_ylabel("Current (A)")
        ax3.set_title("")

        ax4.plot(velocities, voltage/self.battery.voltage)
        ax4.set_ylabel("Throttle (-)")
        ax4.set_title("")

        ax5.plot(velocities, drags/self.total_weight)
        ax5.set_ylabel("Aerodynamic Efficiency (-)")
        ax5.set_title("")

        plt.xlabel("Velocity (km/h)")
        plt.savefig('Outputs/velocity_sweep.pdf')
        plt.close(fig)

    @action
    def export_parameters(self):
        columns = ['Value', 'Unit']
        index = ['Endurance', 'Endurance Mode', 'Velocity', 'Propeller', '# Engines', 'Material', 'Airfoil Root',
                 'Airfoil Tip', 'Airfoil Horizontal Tail', 'Airfoil Vertical Tail', 'Payload Width', 'Payload Length',
                 'Payload Height', 'Payload Weight', 'Battery Capacity', 'Battery Cells',
                 'Motor Name', 'Lift to Drag (design point)']
        values = np.array([self.endurance, self.endurance_mode, self.velocity, self.propeller, self.num_engines,
                           self.structural_material, self.right_wing.airfoil_root, self.right_wing.airfoil_tip,
                           self.horizontal_tail_airfoil_root, self.vertical_tail_airfoil_root, self.payload_width,
                           self.payload_length,
                           self.payload_height, self.payload_weight, self.battery.capacity,
                           self.battery.cells, self.motor_data[self.engines[0].motor.motor_idx, 0],
                           self.total_weight / self.drag])
        units = np.array(['h' if values[1] == 'T' else 'km', np.nan, 'km/h', np.nan, np.nan, np.nan, np.nan, np.nan,
                          np.nan, np.nan, 'm', 'm', 'm', 'N', 'Ah', np.nan, np.nan, np.nan])


        df = pd.DataFrame(np.vstack((values, units)).T, index=index, columns=columns)
        df.to_excel('Outputs/parameters.xlsx')


if __name__ == '__main__':
    data = pd.read_excel('Inputs/Input_data.xlsx')
    data = np.array(data)

    obj = Aircraft(endurance=data[0, 1],
                   endurance_mode=data[1, 1],
                   velocity=data[2, 1],
                   propeller=data[3, 1],
                   num_engines=data[4, 1],
                   structural_material=data[5, 1],
                   airfoil_root=data[6, 1],
                   airfoil_tip=data[7, 1],
                   horizontal_tail_airfoil_root=data[8, 1],
                   horizontal_tail_airfoil_tip=data[8, 1],
                   vertical_tail_airfoil_root=data[9, 1],
                   vertical_tail_airfoil_tip=data[9, 1],
                   payload_width=data[10, 1],
                   payload_length=data[11, 1],
                   payload_height=data[12, 1],
                   payload_weight=data[13, 1]
                )

    # optional inputs
    for i in range(14, data.shape[0]):
        if not np.isnan(data[i, 1]):
            if data[i, 0] == 'Battery Capacity':
                obj.battery_capacity = data[i, 1]
            elif data[i, 0] == 'Battery Cells':
                obj.battery_cells = data[i, 1]

    from parapy.gui import display

    #obj.iterate()
    display(obj)
