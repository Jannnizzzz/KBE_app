
#from parapy.core import Base, Input, Attribute, Part
from parapy.geom import *
from parapy.core import *
from Airfoil import *
from math import *
import matlab.engine
#from Q3D import MATLAB_Q3D_ENGINE
from kbeutils import *

# initialise MATLAB engine
MATLAB_Q3D_ENGINE = matlab.engine.start_matlab()


class Semiwing(LoftedSolid):  # note use of loftedSolid as superclass
    airfoil_root    = Input("whitcomb.dat")
    airfoil_tip     = Input("simm_airfoil.dat")  #: :type: string

    w_c_root        = Input(3)
    w_c_tip         = Input(1)
    t_factor_root   = Input(0.1)
    t_factor_tip    = Input(0.1)

    w_semi_span     = Input(10)
    sweep           = Input(5)
    twist           = Input(2)


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
                           "x", self.w_semi_span * tan(radians(self.sweep))),  # apply sweep
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
    def run_q3d(self):
        """Run Q3D (MATLAB) and get back all results and input"""

        # change matlab root directory to Q3D, so it can find the function
        MATLAB_Q3D_ENGINE.cd(r'..\Q3D')

        return MATLAB_Q3D_ENGINE.run_q3d(
            matlab.double([[0, 0, 0, self.w_c_root, self.twist],
                           [self.w_semi_span*tan(self.sweep), self.w_semi_span, 0, self.w_c_tip, self.twist]
                           ]),

            # in MATLAB 2021, double values are defined as
            # rectangular nested sequence
            matlab.double([1]),

            # define number of outputs if >1
            nargout=2
        )

    @Attribute
    def q3d_res(self) -> dict:
        """q3d results"""
        return self.run_q3d[0]

    @Attribute
    def q3d_ac(self) -> dict:
        """q3d inputs"""
        return self.run_q3d[1]

    @Attribute
    def wing_cl(self) -> float:
        return self.q3d_res["CLwing"]

    @Attribute
    def wing_cd(self) -> float:
        return self.q3d_res["CDwing"]


    print(wing_cl)

if __name__ == '__main__':
    from parapy.gui import display

    obj = Semiwing(label="lifting surface",
                            mesh_deflection=0.0001
                            )
    display(obj)

    #@Part
    #def structure(self):
    #    return Structure()