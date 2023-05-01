
from parapy.core import Base, Input, Attribute, Part

class Wing(Base):
    semi = Input(False)
    w_c_root = Input(6.)  # wing root chord
    w_c_tip = Input(2.3)  # wing tip chord
    w_semi_span = Input(10.)  # wing semi - span
    sweep_TE = Input(20)  # sweep angle, in degrees. Defined at the wing trailing edge (TE)

    @Attribute
    def weight(self):
        return 0#structure(self).weight()

    @Attribute
    def wing_surface_area(self):
        return 0

    @Attribute
    def taper_ratio(self):
        return 0

    @Attribute
    def root_chord(self):
        return 0

    @Attribute
    def cL(self):
        return 0

    @Attribute
    def cD(self):
        return 0

    @Attribute
    def pts(self):
        """ Extract airfoil coordinates from a data file and create a list of 3D points"""
        with open('whitcomb.dat', 'r') as f:
            points = []
            for line in f:
                x, y = line.split(' ', 1)  # separator = " "; max number of split = 1
                # Convert the strings to numbers and make 3D points for the FittedCurve class
                points.append(Point(float(x), float(y)))
        return points

    @Part
    def wing_frame(self):
        return Frame(pos=self.position)  # this helps visualizing the wing local reference frame

    @Part
    def airfoil_from_3D_points(self):  # this curve is on the X-Y plane, with TE = (1, 0, 0) and LE = (0, 0, 0)
        return FittedCurve(points=self.pts,
                           mesh_deflection=0.0001)

    #@Part
    #def structure(self):
    #    return Structure()