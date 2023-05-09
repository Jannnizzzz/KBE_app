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
    payload_weight = Input(2.0)  # in kg

    # fuselage dimensions

    # wing dimensions & parameters


    max_cl          = Input(1.5)
    stall_speed     = Input(40)                        #stall speed in km/h
    #wing_surface_area = Input(1)  # dummy value
    n_ult           = Input(3.0)
    airfoil_root = Input()  # name of the airfoil of the wings root
    airfoil_tip = Input()  # name of the airfoil of the wings root
    #w_c_root = Input(0.5)
    #w_c_tip = Input(0.3)
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

    # __initargs__ = "endurance, endurance_mode, velocity, propeller, num_engines"# , structural_material, " \
    # + "airfoil_root, airfoil_tip"

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

    @Attribute  #based on stall speed for small propeller planes according to CS23
    def wing_surface_area(self):
        return(self.prelim_weight/(0.5*self.max_cl*self.air_density*(self.stall_speed/3.6)**2))

    @Attribute
    def cl_required(self):
        return 1.1* self.prelim_weight / (self.wing_surface_area * 0.5 * self.air_density * self.velocity ** 2)

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
    def total_weight(self):
        return self.prelim_weight + self.wing_weight + self.fuselage_weight

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
        data = pd.read_excel('Motor_data.xlsx')
        data = np.array(data)
        data = data[data[:, 1].argsort()]
        return data

    @Attribute
    def thrust(self):
        surface = self.total_weight / 55
        rho = 1.225
        cD0 = .02
        k = 1 / (np.pi * surface / self.max_width ** 2 * .8)

        return 0.5 * rho * surface * cD0 * (self.velocity / 3.6) ** 2 \
               + 2 * self.total_weight ** 2 * k / (rho * surface * (self.velocity / 3.6) ** 2)

    @Part
    def battery(self):
        return Battery(cap=self.battery_capacity,
                       cells=self.battery_cells)

    @Part
    def fuselage(self):
        return Fuselage(position= translate
                                        (self.position, "x",
                                         self.fuselage.payload_section_length/2,

                        ))

    @Part
    def rectangle(self):
        return Rectangle(width=0.1 * self.fuselage.payload_section_radius,
                         length=2 * child.width,
                         position=translate(
                             rotate90(self.position, 'z'),
                             # self.right_wing.position,
                             'x',
                             self.fuselage.payload_section_length,
                             #'z', child.length * self.dist),

                         #hidden=True
                                  ))

    @Part
    def payload_door(self):  # only one result is visualized, although more wires can result from the operation
        return ProjectedCurve(source=self.rectangle,  # source
                              target=self.fuselage,  # target
                              direction=self.position.Vz)


    @Part
    def engines(self):
        return Engine(quantify=self.num_engines,
                      prop=self.propeller,
                      velocity_op=self.velocity,
                      thrust_op=self.thrust / self.num_engines,
                      max_voltage=self.battery.voltage,
                      voltage_per_cell=self.battery.voltage_per_cell,
                      motor_data=self.motor_data,
                      pos_x=0,
                      pos_y=-(
                                  self.num_engines - 1) * 3 / 4 * self.prop_diameter + child.index * 3 / 2 * self.prop_diameter,
                      pos_z=0 if child.index != (self.num_engines - 1) / 2 else self.prop_diameter * 3 / 4,
                      iteration_history=np.zeros((3,)))

    @Part
    def payload(self):
        return Payload(length=self.payload_length,
                       width=self.payload_width,
                       height=self.payload_height,
                       weight=9.80665 * self.payload_weight,
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

                        visc_option=Input(1),

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

                        visc_option=Input(1),

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

                        visc_option=Input(1),

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

    @action
    def iterate(self):
        any_changes = True

        while any_changes:
            print("=================================")
            print("Total mass", self.total_weight / 9.80665, " kg")
            print("Capacity", self.battery.capacity, " Ah")
            any_changes = False

            # calculate, if the surface area of the wing has to be changed
            required_extra_area = self.total_weight - (
                        self.wing_surface_area * self.air_density * self.cl_required * 0.5 * self.velocity ** 2) / (
                                              self.air_density * self.cl_required * 0.5 * self.velocity ** 2)
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
        plt.plot(self.velocity, self.thrust, 'r*')
        plt.plot([0, self.velocity, self.velocity], [self.thrust, self.thrust, 0], 'k:')
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
        velocity = np.linspace(50, 150, 10)
        drag = 0.05 * (velocity / 3.6) ** 2
        motor_speed, torque, thrust, voltage, current, op_valid = self.engines[0].variable_velocity(velocity,
                                                                                                    drag / self.num_engines)

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

    # obj.iterate()
    obj.velocity_sweep()
    display(obj)
