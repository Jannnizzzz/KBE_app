
#from parapy.core import Base, Input, Attribute, Part
from parapy.geom import *
from parapy.core import *
from Airfoil import *
from math import *


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


if __name__ == '__main__':
    from parapy.gui import display

    obj = Semiwing(label="lifting surface",
                            mesh_deflection=0.0001
                            )
    display(obj)

    #@Part
    #def structure(self):
    #    return Structure()