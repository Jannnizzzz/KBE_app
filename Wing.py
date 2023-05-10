
#from parapy.core import Base, Input, Attribute, Part
from parapy.geom import *
from parapy.core import *
from Airfoil import *
from math import *
import matlab.engine
from _init_ import MATLAB_Q3D_ENGINE
from kbeutils import *
from typing import Dict
from matlab import *

# initialise MATLAB engine
#MATLAB_Q3D_ENGINE = matlab.engine.start_matlab()


class Semiwing(LoftedSolid):  # note use of loftedSolid as superclass
    airfoil_root    = Input("whitcomb.dat")      #: :type: string
    airfoil_tip     = Input("simm_airfoil.dat")  #: :type: string

    wing_surface_area = Input()                  # calculated in aircraft.py
    t_factor_root   = Input(0.1)                 # thickness factor for the airfoil
    t_factor_tip    = Input(0.1)

    w_semi_span     = Input(1.5)                 # wing semi span in [m]
    sweep           = Input(5)                   # sweep angle in deg
    twist           = Input(2)                   # twist angle in deg
    incidence       = Input(3)                   # incidence angle in deg

    dynamic_viscosity   = Input(1.8*10**(-5))    # dynamic viscosity for Reynolds number
    air_density         = Input(1.225)           # density in [kg/m3]
    velocity            = Input(100)             # velocity in [km/h]

    cl                  = Input(0.4)             # design lift coefficient [-]

    visc_option         = Input(1)               #0 for inviscid, 1 for viscous



   # @Attribute
   # def taper_ratio(self):
   #     return(self.w_c_tip/self.w_c_root)

    @Attribute      # based on ADSEE I
    def taper_ratio(self):
        return(0.2*(2-self.sweep*pi/180))

    @Attribute
    def w_c_root(self):     # based on ADSEE I
        return(2*self.wing_surface_area/((1+self.taper_ratio)*self.w_semi_span))

    @Attribute
    def w_c_tip(self):      # based on ADSEE I
        return(self.taper_ratio*self.w_c_root)

    @Attribute
    def mean_aerodynamic_chord(self):  # based on ADSEE I
        return(2/3)*self.w_c_root*(1+self.taper_ratio+self.taper_ratio**2)/(1+self.taper_ratio)


    @Attribute  # required input for the superclass LoftedSolid
    def profiles(self):
        return [self.root_airfoil, self.tip_airfoil]

    @Attribute
    def root_cst(self):     # Get root CST values from the included MATLAB script
        root_data = self.root_airfoil.yt_xl_xu
        return MATLAB_Q3D_ENGINE.demo(matlab.double(root_data), nargout=1)

    @Attribute
    def tip_cst(self):       # get tip CST values from the included MATLAB script
        tip_data = self.tip_airfoil.yt_xl_xu
        return MATLAB_Q3D_ENGINE.demo(matlab.double(tip_data), nargout=1)

    @Part
    def root_airfoil(self):  # root airfoil will receive self.position as default
        return Airfoil(airfoil_name=self.airfoil_root,
                       chord=self.w_c_root,
                       thickness_factor=self.t_factor_root,
                       mesh_deflection=0.0001)

    @Part
    def tip_airfoil(self):      # tip airfoil adjusted for sweep and twist angle
        return Airfoil(airfoil_name=self.airfoil_tip,
                       chord=self.w_c_tip,
                       thickness_factor=self.t_factor_tip,
                       position=translate(
                           rotate(self.position, "y", radians(self.twist)),  # apply twist angle
                           "y", self.w_semi_span,
                           "x", self.w_semi_span * tan(radians(-self.sweep))),  # apply sweep
                       mesh_deflection=0.0001)

    @Part
    def lofted_surf(self):          # define surface for the wing
        return LoftedSurface(profiles=self.profiles,
                             hidden=not (__name__ == '__main__'))

    @Part
    def lofted_solid(self):          # define volume for the wing
        return LoftedSolid(profiles=self.profiles,
                           hidden=not (__name__ == '__main__'))
    @Attribute
    def reynolds_number(self):      # calculate Reynolds number for the Q3D solver
        return[self.air_density*self.velocity*self.mean_aerodynamic_chord/self.dynamic_viscosity]

    @Attribute
    def wing_area(self):            # calculate wing area for Q3D input
        return(0.5*(self.w_c_root+self.w_c_tip)*self.w_semi_span)


    @Attribute
    def run_q3d(self):
        print("Run Q3D")
        """Run Q3D (MATLAB) and get back all results and input"""
        visc_option = self.visc_option
        air_density = self.air_density
        velocity = self.velocity
        cl = self.cl
        reynolds_number = self.air_density*velocity/3.6*self.mean_aerodynamic_chord/self.dynamic_viscosity
        incidence       = self.incidence




        wing_geometry = matlab.double([[0, 0, 0, self.w_c_root, self.twist],
                           [self.w_semi_span*tan(radians(self.sweep)), self.w_semi_span, 0, self.w_c_tip, self.twist]
                           ])
        incidence = matlab.double([incidence])

        #print(wing_geometry, incidence)

        return MATLAB_Q3D_ENGINE.run_q3d(
            wing_geometry,
            matlab.double([incidence]),
            matlab.double([visc_option]),
            matlab.double(self.root_cst),
            matlab.double(self.tip_cst),
            matlab.double([air_density]),
            matlab.double([velocity/3.6]),
            matlab.double([reynolds_number]),
            matlab.double([cl]),
            nargout=2
        )

    def variable_run_q3d(self, velocity, cl):
        print("Run Q3D")
        """Run Q3D (MATLAB) and get back all results and input"""
        visc_option = self.visc_option
        air_density = self.air_density
        reynolds_number = self.air_density*velocity/3.6*self.mean_aerodynamic_chord/self.dynamic_viscosity
        incidence       = self.incidence




        wing_geometry = matlab.double([[0, 0, 0, self.w_c_root, self.twist],
                           [self.w_semi_span*tan(radians(self.sweep)), self.w_semi_span, 0, self.w_c_tip, self.twist]
                           ])
        incidence = matlab.double([incidence])

        return MATLAB_Q3D_ENGINE.run_q3d(
            wing_geometry,
            matlab.double([incidence]),
            matlab.double([visc_option]),
            matlab.double(self.root_cst),
            matlab.double(self.tip_cst),
            matlab.double([air_density]),
            matlab.double([velocity/3.6]),
            matlab.double([reynolds_number]),
            matlab.double([cl]),
            nargout=2
        )

    @Attribute
    def q3d_res(self) -> Dict:
        """q3d results"""
        return self.run_q3d[0]

    def variable_q3d_res(self, velocity, cl) -> Dict:
        """q3d results"""
        return self.variable_run_q3d(velocity, cl)[0]

    def q3d_ac(self, velocity, cl) -> Dict:
        """q3d inputs"""
        return self.variable_run_q3d(velocity, cl)[1]

    @Attribute
    def wing_cl(self) -> float:
        return self.q3d_res["CLwing"]

    def variable_wing_cd(self, velocity, cl) -> float:
        return self.variable_q3d_res(velocity, cl)["CDwing"]

    @Attribute
    def wing_cd(self) -> float:
        return self.q3d_res["CDwing"]

    def wing_alfa(self, velocity) -> float:
        return self.variable_q3d_res(velocity)["Alfa"]


    #print(wing_cl)

if __name__ == '__main__':
    from parapy.gui import display
    obj = Semiwing(label="Wing",
                            mesh_deflection=0.0001
                            )
    display(obj)

