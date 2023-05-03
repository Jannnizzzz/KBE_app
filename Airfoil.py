#from kbeutils.geom.curve import Naca5AirfoilCurve, Naca4AirfoilCurve
from parapy.geom import *
from parapy.core import *
import os.path



class Airfoil(FittedCurve):  # note the use of FittedCurve as superclass
    airfoil_name = Input()                  # NACA airfoil generator
    chord = Input()
    thickness_factor = Input()
    mesh_deflection = Input()
    tolerance = 0.0001

#    @Part
#    def airfoil(self):
#        return DynamicType(type=(Naca5AirfoilCurve
#                                 if len(self.airfoil_name) == 5
#                                 else Naca4AirfoilCurve),
#                           designation=self.airfoil_name)

    @Attribute
    def points(self):  # required input to the FittedCurve superclass
        if self.airfoil_name.endswith('.dat'):  # check whether the airfoil name string includes .dat already
            airfoil_file = self.airfoil_name
        else:
            airfoil_file = self.airfoil_name + '.dat'
        file_path = os.path.join('Airfoil_data', airfoil_file)
        with open(file_path, 'r') as f:
            point_lst = []
            for line in f:
                x, z = line.split(' ', 1)  # the cartesian coordinates are directly interpreted as X and Z coordinates
                point_lst.append(self.position.translate(
                    "x", float(x) * self.chord,  # the x points are scaled according to the airfoil chord length
                    "z", float(z) * self.chord * self.thickness_factor))  # the y points are scaled according to the /
                # thickness factor
        return point_lst


if __name__ == '__main__':
    from parapy.gui import display

    obj = Airfoil(label="airfoil")
    display(obj)
