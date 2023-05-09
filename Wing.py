
#from parapy.core import Base, Input, Attribute, Part
from parapy.geom import *
from parapy.core import *
from Airfoil import *
from math import *
import matlab.engine
#from Q3D import MATLAB_Q3D_ENGINE
from kbeutils import *
from typing import Dict
from matlab import *

# initialise MATLAB engine
MATLAB_Q3D_ENGINE = matlab.engine.start_matlab()


class Semiwing(LoftedSolid):  # note use of loftedSolid as superclass
    airfoil_root    = Input("whitcomb.dat")
    airfoil_tip     = Input("simm_airfoil.dat")  #: :type: string

    #w_c_root        = Input(0.5)
    #w_c_tip         = Input(0.3)
    wing_surface_area = Input()
    t_factor_root   = Input(0.1)
    t_factor_tip    = Input(0.1)

    w_semi_span     = Input(1.5)
    sweep           = Input(5)
    twist           = Input(2)
    incidence       = Input(3)

    dynamic_viscosity   = Input(1.8*10**(-5))
    air_density         = Input(1.225)
    velocity            = Input(100)

    cl                  = Input(0.4)

    visc_option         = Input(1) #0 for inviscid, 1 for viscous



   # @Attribute
   # def taper_ratio(self):
   #     return(self.w_c_tip/self.w_c_root)

    @Attribute
    def taper_ratio(self):
        return(0.2*(2-self.sweep*pi/180))

    @Attribute
    def w_c_root(self):
        return(2*self.wing_surface_area/((1+self.taper_ratio)*self.w_semi_span))

    @Attribute
    def w_c_tip(self):
        return(self.taper_ratio*self.w_c_root)

    @Attribute
    def mean_aerodynamic_chord(self):
        return(2/3)*self.w_c_root*(1+self.taper_ratio+self.taper_ratio**2)/(1+self.taper_ratio)


    @Attribute  # required input for the superclass LoftedSolid
    def profiles(self):
        return [self.root_airfoil, self.tip_airfoil]

    @Part
    def root_airfoil(self):  # root airfoil will receive self.position as default
        return Airfoil(airfoil_name=self.airfoil_root,
                       chord=self.w_c_root,
                       thickness_factor=self.t_factor_root,
                       mesh_deflection=0.0001)

    @Part
    def tip_airfoil(self):
        return Airfoil(airfoil_name=self.airfoil_tip,
                       chord=self.w_c_tip,
                       thickness_factor=self.t_factor_tip,
                       position=translate(
                           rotate(self.position, "y", radians(self.twist)),  # apply twist angle
                           "y", self.w_semi_span,
                           "x", self.w_semi_span * tan(radians(-self.sweep))),  # apply sweep
                       mesh_deflection=0.0001)

    @Part
    def lofted_surf(self):
        return LoftedSurface(profiles=self.profiles,
                             hidden=not (__name__ == '__main__'))

    @Part
    def lofted_solid(self):
        return LoftedSolid(profiles=self.profiles,
                           hidden=not (__name__ == '__main__'))
    @Attribute
    def reynolds_number(self):
        return[self.air_density*self.velocity*self.mean_aerodynamic_chord/self.dynamic_viscosity]

    @Attribute
    def wing_area(self):
        return(0.5*(self.w_c_root+self.w_c_tip)*self.w_semi_span)


    @Attribute
    def run_q3d(self):
        """Run Q3D (MATLAB) and get back all results and input"""

        # change matlab root directory to Q3D, so it can find the function
        MATLAB_Q3D_ENGINE.cd(r'Q3D')

        root_data = self.root_airfoil.yt_xl_xu
        tip_data = self.tip_airfoil.yt_xl_xu
        visc_option = self.visc_option
        velocity    = self.velocity
        air_density = self.air_density
        reynolds_number = self.reynolds_number
        incidence       = self.incidence
        cl              = self.cl




        wing_geometry = matlab.double([[0, 0, 0, self.w_c_root, self.twist],
                           [self.w_semi_span*tan(radians(self.sweep)), self.w_semi_span, 0, self.w_c_tip, self.twist]
                           ])
        incidence = matlab.double([incidence])

        #print(wing_geometry, incidence)

        return MATLAB_Q3D_ENGINE.run_q3d(
            wing_geometry,
            incidence,
            visc_option,
            matlab.double(root_data),
            matlab.double(tip_data),
            matlab.double([air_density]),
            matlab.double([velocity]),
            matlab.double([reynolds_number]),
            matlab.double([cl]),
            nargout=2
        )

    @Attribute
    def q3d_res(self) -> Dict:
        """q3d results"""
        return self.run_q3d[0]

    @Attribute
    def q3d_ac(self) -> Dict:
        """q3d inputs"""
        return self.run_q3d[1]

    @Attribute
    def wing_cl(self) -> float:
        return self.q3d_res["CLwing"]

    @Attribute
    def wing_cd(self) -> float:
        return self.q3d_res["CDwing"]

    @Attribute
    def wing_alfa(self) -> float:
        return self.q3d_res["Alfa"]


    #print(wing_cl)

if __name__ == '__main__':
    from parapy.gui import display
    obj = Semiwing(label="Wing",
                            mesh_deflection=0.0001
                            )
    display(obj)

    #@Part
    #def structure(self):
    #    return Structure()