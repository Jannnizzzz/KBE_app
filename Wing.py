
from parapy.core import Base, Input, Attribute, Part

class Wing(Base):
    semi = Input(False)
    w_c_root = Input(6.)  # wing root chord
    w_c_tip = Input(2.3)  # wing tip chord
    w_semi_span = Input(10.)  # wing semi - span
    sweep_TE = Input(20)  # sweep angle, in degrees. Defined at the wing trailing edge (TE)

    @Attribute
    def sweep(self):
        return[0]                   #implement mach number relationship

    @Attribute
    def weight(self):
        return 0                    #structure(self).weight()

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
        with open('whitcomb.dat', 'r') as f:                                                        #Add proper airfoil selection here
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


    @Part  # TransformedCurve is making a carbon copy of the fitted curve, which can be moved (rotated and translated) /
    # from one position to another. /
    # In this case we want to position the fitted curve copy in the x-z plane of the wing reference system, with its /
    # TE in the origin (location) of this reference system. This requires a rotation and a few translations.
    def root_section_unscaled(self):
        return TransformedCurve(
            curve_in=self.airfoil_from_3D_points,
            # the curve to be repositioned
            from_position=rotate(translate(XOY, 'x', 1), 'x', -90, deg=True),
            to_position=self.position,  # The wing relative reference system
            hidden=False
        )

    @Part  # for the wing tip we use the same type of airfoil used for the wing root. We use again TransformedCurve
    def tip_section_unscaled(self):
        return TransformedCurve(
            curve_in=self.root_section_unscaled,
            # the curve to be repositioned
            from_position=self.root_section_unscaled.position,
            to_position=translate(self.root_section_unscaled.position,  # to_position, i.e. the wing tip section
                                  'y', self.w_semi_span,
                                  'x', self.w_semi_span * tan(radians(self.sweep_TE))
                                  ),  # the sweep is applied
            hidden=True
        )

    @Part
    def root_section(self):  # the ScaledCurve primitive allows scaling a given curve. Here it is used to scale /
        # the unit chord airfoil generated from the .dat file according to their actual chord length
        return ScaledCurve(
            curve_in=self.root_section_unscaled,
            reference_point=self.root_section_unscaled.start,  # this point (the curve TE in this case) / is kept fixed during scaling
            factor=self.w_c_root,  # uniform scaling
            mesh_deflection=0.0001
        )

    @Part
    def tip_section(self):
        return ScaledCurve(
            curve_in=self.tip_section_unscaled,
            reference_point=self.tip_section_unscaled.start,
            factor=self.w_c_tip
        )

    @Part
    def wing_loft_surf(self):  # generate a surface
        return LoftedSurface(
            profiles=[self.root_section, self.tip_section],
            mesh_deflection=0.0001
        )

    @Part
    def wing_loft_solid(self):  # generate a solid
        return LoftedSolid(
            profiles=[self.root_section, self.tip_section],
            mesh_deflection=0.0001
        )


    #@Part
    #def structure(self):
    #    return Structure()